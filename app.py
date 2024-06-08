import gradio as gr
from tools.fetch_stock_info import anazlyze_stock


demo = gr.Interface(
    fn=anazlyze_stock,
    inputs=["text", "checkbox"],
    outputs=[
        gr.Textbox(label="Company Name"),
        gr.Textbox(label="Stock History (Will be shown if `detailed`)"),
        gr.Textbox(label="Stock Fanancials (Will be shown if `detailed`)"),
        gr.Textbox(label="Stock News (Will be shown if `detailed`)"),
        gr.Textbox(label="Final Analysis"),
    ],
)

if __name__ == "__main__":
    demo.launch(share=True)
