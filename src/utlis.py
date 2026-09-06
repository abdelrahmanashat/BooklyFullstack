from fasthtml.common import *
from pydantic import BaseModel
from datetime import date
import inspect
from functools import wraps

def generate_form_from_model(model: BaseModel, submit_url: str, submit_text: str = "Submit") -> Form:
    """Dynamically generates a FastHTML Form from a Pydantic model."""
    inputs = []
    
    for field_name, field_info in model.model_fields.items():
        # 1. Determine the HTML input type based on the Python type annotation
        field_type = field_info.annotation
        html_type = "text" # default
        
        if field_type == int:
            html_type = "number"
        elif field_type == date:
            html_type = "date"
        elif "password" in field_name.lower():
            html_type = "password"
        elif "email" in field_name.lower():
            html_type = "email"
            
        # 2. Extract constraints (like max_length from your UserCreateModel)
        max_len = None
        for metadata in field_info.metadata:
            if hasattr(metadata, 'max_length'):
                max_len = metadata.max_length
                
        # 3. Build the FastHTML Input and Label
        input_kwargs = {"name": field_name, "type": html_type, "required": field_info.is_required()}
        if max_len:
            input_kwargs["maxlength"] = max_len
            
        # Format the label nicely (e.g., "first_name" -> "First Name")
        label_text = field_name.replace("_", " ").title()
        
        inputs.append(
            Label(label_text, Input(**input_kwargs))
        )
        
    # Add the submit button and wrap in a Form
    inputs.append(Button(submit_text, type="submit"))
    return Form(*inputs, action=submit_url, method="post")

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