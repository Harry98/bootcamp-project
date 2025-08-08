import gradio as gr
from graph import execute_user_query
import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


demo = gr.ChatInterface(
    execute_user_query,
    type="messages",
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    save_history=True,
)

if __name__ == "__main__":
    demo.launch()
