import os
from openai import OpenAI
from git import Repo

# 配置智谱 GLM-4.7-Flash
client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

repo = Repo(".")

# 获取本次推送变更的代码文件
try:
    changed_files = [
        item.a_path for item in repo.head.commit.diff('HEAD~1')
        if item.a_path.endswith(('.java', '.py', '.js', '.ts', '.cpp', '.go', '.c', '.h'))
    ]
except ValueError:
    # 如果是第一次提交，没有 HEAD~1，就处理所有文件
    changed_files = [
        f for f in repo.git.ls_files().split('\n')
        if f.endswith(('.java', '.py', '.js', '.ts', '.cpp', '.go', '.c', '.h'))
    ]

for fpath in changed_files:
    if not os.path.exists(fpath):
        continue
    
    print(f"正在处理: {fpath}")
    
    # 读取原代码
    with open(fpath, 'r', encoding='utf-8') as f:
        code = f.read()

    # 构建提示词，要求 GLM 加中文注释
    prompt = f"""请为以下代码的所有函数、类添加规范的中文注释。
    要求：
    1. 说明函数/类的作用、入参含义、返回值含义
    2. 不修改任何原有代码逻辑
    3. 仅输出完整的带注释代码，不要任何额外说明
    4. 注释风格符合对应语言的规范（如 Python 用 docstring，Java 用 Javadoc 风格）

    代码如下：
    {code}
    """

    try:
        # 调用 GLM-4.7-Flash
        res = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        new_code = res.choices[0].message.content
        
        # 清理可能的 Markdown 代码块标记
        new_code = new_code.replace("```java", "").replace("```python", "")
        new_code = new_code.replace("```cpp", "").replace("```c", "").replace("```", "")
        new_code = new_code.strip()

        # 写回文件
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        print(f"处理完成: {fpath}")

    except Exception as e:
        print(f"处理失败 {fpath}: {e}")
        continue
