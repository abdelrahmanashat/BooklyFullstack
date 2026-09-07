from fasthtml.common import Form, Label, Input, Button, Div, Span
from pydantic import BaseModel
from datetime import date
import inspect
from functools import wraps

def generate_form_from_model(model: BaseModel, submit_url: str, submit_text: str = "Submit", initial_data: dict = None
) -> Form:
    """Dynamically generates a UI/UX friendly FastHTML Form from a Pydantic model."""
    inputs = []
    initial_data = initial_data or {} 
    
    for field_name, field_info in model.model_fields.items():
        # 1. Determine the HTML input type
        field_type = field_info.annotation
        html_type = "text"
        
        if field_type == int:
            html_type = "number"
        elif field_type == date:
            html_type = "date"
        elif "password" in field_name.lower():
            html_type = "password"
        elif "date" in field_name.lower():
            html_type = "date_str"
        elif "email" in field_name.lower():
            html_type = "email"
            
        # Extract max length if available
        max_len = None
        for metadata in field_info.metadata:
            if hasattr(metadata, 'max_length'):
                max_len = metadata.max_length
                
        is_req = field_info.is_required()
        label_text = field_name.replace("_", " ").title()
        
        # UX Feature: Smart Placeholders
        placeholder_text = f"Enter {label_text.lower()}" 
        if html_type == "date":
            placeholder_text = ""
        elif html_type == "date_str":
            placeholder_text = "Enter date in the form yyyy-mm-dd"
        elif html_type == "password":
            placeholder_text = "••••••••"
        
        # Build core input style string
        input_style = "margin-top: 0.4rem; padding: 0.6rem; border-radius: 6px; width: 100%;"
        if html_type == "password":
            # Add right padding so text doesn't hide behind the absolute-positioned icon
            input_style += " padding-right: 2.5rem;"
        
        input_kwargs = {
            "name": field_name, 
            "type": html_type, 
            "required": is_req,
            "placeholder": placeholder_text,
            "style": "margin-top: 0.4rem; padding: 0.6rem; border-radius: 6px;" # Softens the input boxes
        }
        
        if max_len:
            input_kwargs["maxlength"] = max_len
            
        # Inject pre-filled data if available
        if field_name in initial_data and initial_data[field_name] is not None:
            input_kwargs["value"] = str(initial_data[field_name])
            
        # UX Feature: Visual Required/Optional Badges
        req_badge = Span(" *", style="color: #ef4444; font-weight: bold;") if is_req else Span(" (Optional)", style="color: #94a3b8; font-size: 0.85em; font-weight: normal; margin-left: 4px;")
        
        # Build the input element
        input_element = Input(**input_kwargs)
        
        # UX Feature: Dynamic Password Visibility Toggle
        if html_type == "password":
            input_field_layout = Div(
                input_element,
                Button(
                    "👁️", 
                    type="button", 
                    id=f"toggle-{field_name}",
                    onclick="""
                        const passwordInput = this.previousElementSibling;
                        if (passwordInput.type === 'password') {
                            passwordInput.type = 'text';
                            this.textContent = '🙈';
                        } else {
                            passwordInput.type = 'password';
                            this.textContent = '👁️';
                        }
                    """,
                    style="position: absolute; right: 10px; top: 58%; transform: translateY(-50%); background: none; border: none; padding: 0; cursor: pointer; font-size: 1.1rem; box-shadow: none;"
                ),
                style="position: relative; width: 100%;"
            )
        else:
            input_field_layout = input_element
        
        # UX Feature: Vertical Spacing & Label Formatting
        inputs.append(
            Div(
                Label(
                    Span(label_text, style="font-weight: 600; color: #334155;"),
                    req_badge,
                    input_field_layout
                ),
                style="margin-bottom: 1.25rem;" # Adds breathing room between fields
            )
        )
        
    # UX Feature: Prominent, full-width Action Button
    inputs.append(
        Button(
            submit_text, 
            type="submit", 
            cls="button primary",
            style="width: 100%; margin-top: 10px; padding: 0.75rem; font-size: 1.05rem; font-weight: 600; border-radius: 8px; cursor: pointer;"
        )
    )
    
    # UX Feature: Clean Card Container Layout
    return Form(
        *inputs, 
        action=submit_url, 
        method="post",
        style="width: 100%; max-width: 500px; margin: 0 auto; padding: 25px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
    )

# The dynamic decorator updated to handle async routes seamlessly
def accept_model_fields(model: type[BaseModel]):
    def decorator(func):
        # 1. Get the parameter you explicitly typed out (like 'token')
        existing_sig = inspect.signature(func)
        existing_params = list(existing_sig.parameters.values())

        # Keep everything except standard **kwargs catch-alls
        existing_params = [
            p
            for p in existing_params
            if p.kind not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
        ]

        # 2. Extract explicit names to prevent adding them twice
        explicit_names = {p.name for p in existing_params}

        # 3. Generate dynamic parameters as standard POSITIONAL_OR_KEYWORD fields
        model_params = [
            inspect.Parameter(
                name=name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,  # Kept uniform with explicit params
                annotation=field_info.annotation,
                default=(
                    field_info.default
                    if field_info.default is not inspect.Signature.empty
                    else inspect.Parameter.empty
                ),
            )
            for name, field_info in model.model_fields.items()
            if name not in explicit_names
        ]

        # 4. Combine them (explicit parameters take priority at the front)
        final_params = existing_params + model_params

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper.__signature__ = inspect.Signature(final_params)
        return wrapper

    return decorator