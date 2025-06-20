from pydantic import BaseModel, Field
from typing import Optional


class WeatherRequest(BaseModel):
    """Modèle pour la requête météo"""
    ville: str = Field(..., description="Nom de la ville pour laquelle obtenir la météo")


class WeatherResponse(BaseModel):
    """Modèle pour la réponse météo"""
    ville: str
    conditions: str
    temperature: str
    description: str


def get_weather(request: WeatherRequest) -> WeatherResponse:
    """
    Outil météo qui retourne toujours qu'il fait beau !
    
    Args:
        request: WeatherRequest contenant le nom de la ville
    
    Returns:
        WeatherResponse avec les informations météo (toujours beau temps)
    """
    return WeatherResponse(
        ville=request.ville,
        conditions="Ensoleillé ☀️",
        temperature="25°C",
        description=f"Il fait un temps magnifique à {request.ville} ! Le soleil brille et il fait une température parfaite de 25°C."
    )