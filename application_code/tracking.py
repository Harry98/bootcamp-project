import functools
from typing import Callable, Any, Coroutine, Dict
from langfuse import get_client
from llm import GEMINI_FLASH

langfuse_client = get_client()


def track_llm_generation(name: str, model_name: str = GEMINI_FLASH):
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            print(f"Starting Tracing for: {name}")
            state = args[0] if args else kwargs.get("state")

            try:
                with langfuse_client.start_as_current_span(
                        name=name,
                        input=state,
                        metadata={'model': model_name}
                ) as span:

                    span.update_trace(
                        session_id=state['session_id'],
                        tags=[f"{name}"]
                    )

                    with langfuse_client.start_as_current_generation(name=f"llm_gen_{name}",
                                                                     model=model_name) as generation:
                        result = await func(*args, **kwargs)
                        print(f"Tracing Output of the {name} is {result}.")
                        if 'token_usage' in result:
                            print(f"Tokens used {name} are {result['token_usage']}")

                            generation.update(
                                output=result,
                                input=state,
                                usage_details=result['token_usage']
                            )

                            span.update(
                                output=result,
                                input=state
                            )

                            span.update_trace(
                                output=result,
                                input=state
                            )

                        print(f"Completed Tracing for: {name}")
                        return result

            except Exception as e:
                # Log error to langfuse
                langfuse_client.update_current_trace(
                    tags=[name, "error"],
                    output={"error": str(e)},
                    session_id=state.get('session_id') if state else None
                )
                print(f"Error in Tracing for: {name} - {str(e)}")
                raise  # Re-raise the exception

        return wrapper

    return decorator
