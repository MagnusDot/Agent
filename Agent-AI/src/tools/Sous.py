from langchain_core.tools import tool


@tool
def Sous(first: int, second: int) -> int:
    """
    Outil qui soustrait deux entiers.
    
    Args:
        first: Premier nombre entier
        second: Deuxième nombre entier
    
    Returns:
        La différence entre le premier et le deuxième nombre (first - second)
    """
    return first - second