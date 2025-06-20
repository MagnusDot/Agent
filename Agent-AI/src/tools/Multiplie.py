from langchain_core.tools import tool


@tool
def Multiple(first: int, second: int) -> int:
    """
    Outil qui Multiplication deux entiers.
    
    Args:
        first: Premier nombre entier
        second: Deuxième nombre entier
    
    Returns:
        La Multiplication entre le premier et le deuxième nombre (first - second)
    """
    return first * second