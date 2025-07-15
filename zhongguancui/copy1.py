from openai import OpenAI
from datetime import datetime


class RolePlayingSystem:
    def __init__(self):
        # 初始化客户端

        self.user_client = OpenAI(api_key="sk-8b4fbda85112496b8f6f2dc2fe489d25",
                                  base_url="https://api.deepseek.com")
        self.npc1_client = OpenAI(api_key="sk-d50cff82fe3b4dd19a26ada8d9344efb",
                                  base_url="https://api.deepseek.com")
        self.npc2_client = OpenAI(api_key="sk-a4f0e259f3844c08b822a402e5453092",
                                  base_url="https://api.deepseek.com")
        self.summary_client = OpenAI(api_key="sk-9dd89e44713049c39b467039f9455bd7",
                                     base_url="https://api.deepseek.com")

        self.scenario = None
        self.npc1_setup = None
        self.npc2_setup = None
        self.script = []
        self.history_file = "text.txt"

    def initialize_scenario(self):
        """初始化故事场景和角色"""
        print("请设定故事背景和两个NPC角色：")
        self.scenario = input("故事背景：")
        self.npc1_setup = input("NPC1角色设定（身份/性格/目标）：")
        self.npc2_setup = input("NPC2角色设定（身份/性格/目标）：")

        # 初始化历史文件
        with open(self.history_file, 'w', encoding='utf-8') as f:
            f.write(f"场景设定：{self.scenario}\n")
            f.write(f"角色设定：NPC1-{self.npc1_setup}, NPC2-{self.npc2_setup}\n\n")

        self.script.extend([
            f"【场景】{self.scenario}",
            f"【NPC1】{self.npc1_setup}",
            f"【NPC2】{self.npc2_setup}"
        ])

    def read_file_safe(self, filename):
        """安全读取文件内容"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"警告：历史文件 {filename} 未找到，将创建新文件")
            return ""
        except Exception as e:
            print(f"读取文件错误：{str(e)}")
            return ""

    def generate_summary(self, new_content):
        """生成对话总结并保存"""
        prompt = f"""请用100字内总结以下对话内容，保持故事连贯性：
        当前场景：{self.scenario}
        最新对话：{new_content}
        历史上下文：{self.read_file_safe(self.history_file)}"""

        response = self.summary_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content

    def npc_response(self, client, setup, user_action):
        """生成NPC响应"""
        history = self.read_file_safe(self.history_file)
        prompt = f"""角色设定：{setup}
        场景背景：{self.scenario}
        历史对话：{history[-500:]}
        面对主角行为：{user_action}
        请用1-2句话做出符合角色的反应（对话+动作）"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

    def run_interaction(self):
        """主交互循环"""
        while True:
            user_input = input("【主角行动】你的行动/对话：")
            if user_input.lower() == 'exit':
                break

            self.script.append(f"主角：{user_input}")

            # 获取NPC响应
            npc1_res = self.npc_response(self.npc1_client, self.npc1_setup, user_input)
            npc2_res = self.npc_response(self.npc2_client, self.npc2_setup, user_input)

            print(f"NPC1 → {npc1_res}")
            print(f"NPC2 → {npc2_res}")

            # 记录到剧本
            interaction = f"\n主角：{user_input}\nNPC1：{npc1_res}\nNPC2：{npc2_res}"
            self.script.extend([f"NPC1：{npc1_res}", f"NPC2：{npc2_res}"])

            # 生成并保存总结
            summary = self.generate_summary(interaction)
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(interaction + "\n")
                f.write(f"当前总结：{summary}\n")

    def save_script(self):
        """保存完整剧本"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"script_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.script))
        print(f"剧本已保存为 {filename}")


if __name__ == "__main__":
    rpg = RolePlayingSystem()
    rpg.initialize_scenario()
    print("\n=== 开始互动（输入exit退出）===")
    rpg.run_interaction()
    rpg.save_script()
