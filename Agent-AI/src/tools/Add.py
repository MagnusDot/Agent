from langchain_core.tools import tool

@tool
def Add(first: int, second: int) -> int:
    """
    Outil qui additionne deux entiers.
    
    Args:
        first: Premier nombre entier
        second: Deuxième nombre entier
    
    Returns:
        La somme des deux nombres
    """
    return first + second