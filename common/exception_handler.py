from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """
    Manejador personalizado de excepciones para formatear errores de validación
    de una manera más legible para el cliente.
    """
    response = exception_handler(exc, context)

    # Si hay una respuesta y es un error de validación (400 Bad Request)
    if response is not None and response.status_code == 400:
        data = response.data
        formatted_errors = []

        # Si 'data' es un diccionario (ej: {"email": ["Error 1"], "password": ["Error 2"]})
        if isinstance(data, dict):
            for field, errors in data.items():
                # Obtenemos el primer error de la lista si es una lista
                error_msg = errors[0] if isinstance(errors, list) else str(errors)
                
                # Caso especial: 'non_field_errors' (errores generales)
                if field == 'non_field_errors':
                    formatted_errors.append(error_msg)
                else:
                    # Formato legible: "Email: Error 1"
                    formatted_errors.append(f"{field.capitalize()}: {error_msg}")
            
            # Reemplazamos la data original con nuestro formato simple
            response.data = {
                "message": "\n".join(formatted_errors), # Un solo string con saltos de línea
                "original_errors": data # Mantenemos el original por si acaso (opcional)
            }
        
        # Si 'data' es una lista (ej: errores múltiples sin campo específico)
        elif isinstance(data, list):
            response.data = {
                "message": data[0]
            }

    return response