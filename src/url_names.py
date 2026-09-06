class URLNames:
    title:str = "Bookly"
    version:str = "v1"
    description:str = """
    A REST API for a book review web service.

    This REST API is able to;
    - Create Read Update And delete books
    - Add reviews to books
    - Add tags to Books e.t.c.
    """
    version_prefix:str = f"/api/{version}"
    license_info:dict = {"name": "MIT License", "url": "https://opensource.org/license/mit"}
    contact:dict = {
        "name": "Abdelrahman Nasat",
        "url": "https://github.com/abdelrahmanashat/",
        "email": "abdelrahmanashat@gmail.com",
    }
    terms_of_service:str = "https://example.com/tos"
    openapi_url:str = f"{version_prefix}/openapi.json"
    docs_url:str = f"{version_prefix}/docs"
    redoc_url:str = f"{version_prefix}/redoc"
    frontend_url:str = "/ui"

url_names = URLNames() 