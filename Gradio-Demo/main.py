import gradio as gr

# 保留两个独立函数（无需整合）
def text_transform(text, transform_type):
    if transform_type == "大写":
        return text.upper()
    elif transform_type == "小写":
        return text.lower()
    elif transform_type == "首字母大写":
        return text.title()
    elif transform_type == "反转":
        return text[::-1]
    else:
        return text

def text_statistics(text):
    char_count = len(text)
    word_count = len(text.split()) if text.strip() else 0
    line_count = text.count("\n") + 1 if text else 0
    return f"字符数：{char_count}\n单词数：{word_count}\n行数：{line_count}"

# 使用Blocks创建灵活界面（支持多按钮绑定不同函数）
def create_interface():
    with gr.Blocks(title="文本工具（多按钮版）") as demo:
        gr.Markdown("# 文本处理工具")  # 标题
        
        # 共用的文本输入框
        input_text = gr.Textbox(label="输入文本", placeholder="请输入文本...", lines=4)
        
        # 第一个功能区：文本转换
        with gr.Tab("文本转换"):  # 用Tab分栏，更清晰
            transform_type = gr.Radio(
                label="转换类型",
                choices=["大写", "小写", "首字母大写", "反转"],
                value="大写"
            )
            output_transform = gr.Textbox(label="转换结果", lines=4)
            # 绑定按钮到text_transform函数
            btn_transform = gr.Button("执行转换")
            btn_transform.click(
                fn=text_transform,
                inputs=[input_text, transform_type],
                outputs=output_transform
            )
        
        # 第二个功能区：文本统计
        with gr.Tab("文本统计"):
            output_stat = gr.Textbox(label="统计结果", lines=4)
            # 绑定按钮到text_statistics函数
            btn_stat = gr.Button("执行统计")
            btn_stat.click(
                fn=text_statistics,
                inputs=[input_text],
                outputs=output_stat
            )
    
    return demo

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=False)