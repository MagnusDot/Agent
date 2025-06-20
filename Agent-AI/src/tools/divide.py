from langchain_core.tools import tool


@tool
def Divide(first: int, second: int) -> int:
    """
    Outil qui Divise deux entiers.
    
    Args:
        first: Premier nombre entier
        second: Deuxième nombre entier
    
    Returns:
        La Division entre le premier et le deuxième nombre (first - second)
    """
    return first / second