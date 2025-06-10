import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import requests


class PTAContestGenerator:
    def __init__(self):  # 修改构造函数
        self.session = requests.Session()
        self.selected_problem_set_id = None
        self.contest_root = None
        self.label_map = {}
        self.exam_info = {}
        self._configure_session()

    def set_cookies(self, cookies):
        """更新会话的Cookie信息"""
        self.session.cookies.update(cookies)


    def _configure_session(self):
        """配置会话参数"""
        headers = \
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Referer": "https://pintia.cn/",
                "Accept": "application/json, text/plain, */*"
            }

        self.session.headers.update(headers)

    @staticmethod
    def generate_letters(n):
        """生成题目字母序号"""
        return [chr(65 + i) for i in range(n)]

    @staticmethod
    def indent(elem, level=0):
        """XML格式化工具"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                PTAContestGenerator.indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def get_problem_sets(self):
        """获取所有可用题目集"""
        all_sets = []
        page = 0
        limit = 50

        while True:
            url = f"https://pintia.cn/api/problem-sets/admin?sort_by=%7B%22type%22%3A%22UPDATE_AT%22%2C%22asc%22%3Afalse%7D&page={page}&limit={limit}&filter=%7B%22ownerId%22%3A%220%22%7D"
            resp = self.session.get(url)
            print(self.session.cookies.get_dict())
            if resp.status_code != 200:
                raise Exception(f"请求失败，状态码：{resp.status_code}")

            data = resp.json()
            current = data.get("problemSets", [])
            all_sets.extend(current)

            if len(current) < limit:
                break
            page += 1

        return [{
            "name": ps.get("name", "未命名题目集"),
            "id": ps.get("id"),
            "start_time": ps.get("startAt"),
        } for ps in all_sets]

    def select_problem_set(self, problem_set_id):
        """选择目标题目集"""
        self.selected_problem_set_id = problem_set_id
        self._validate_problem_set()

    def _validate_problem_set(self):
        """验证题目集有效性"""
        if not self.selected_problem_set_id:
            raise ValueError("未选择题目集")
        test_url = f"https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/exams"
        resp = self.session.get(test_url)
        if resp.status_code != 200:
            raise ValueError("无效的题目集ID")

    def generate_contest_xml(self, output_path="contest.xml"):
        """生成比赛XML文件"""
        self._init_xml_structure()
        self._process_exam_info()
        self._add_static_nodes()
        self._process_problems()
        self._process_teams()
        self._process_submissions()
        self._add_finalized_node()
        self._save_xml(output_path)
        return output_path

    def _init_xml_structure(self):
        """初始化XML根节点"""
        self.contest_root = ET.Element("contest")

    # def _process_exam_info(self):
    #     """处理考试基础信息"""
    #     # url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/exams' 为学生端接口
    #     url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}'
    #     resp = self.session.get(url)
    #     self.exam_info = resp.json()
    #
    #     info = ET.SubElement(self.contest_root, "info")
    #     problem_set = self.exam_info.get("problemSet", {})
    #
    #     # 时间处理
    #     start_at = problem_set.get("startAt", "2025-05-16T00:00:00Z")
    #     start_time = datetime.fromisoformat(start_at.replace('Z', '+00:00')).timestamp()
    #
    #     # 添加子节点
    #     ET.SubElement(info, "length").text = self.exam_info.get("duration", "4:00:00")
    #     ET.SubElement(info, "penalty").text = str(self.exam_info.get("penalty_minutes", 20))    # 罚时自定义设置
    #     ET.SubElement(info, "started").text = "False"
    #     ET.SubElement(info, "starttime").text = f"{start_time:.1f}"
    #     ET.SubElement(info, "title").text = self.exam_info.get("name", "默认比赛")
    #     ET.SubElement(info, "short-title").text = self.exam_info.get("short_title", "Default Contest")
    #     ET.SubElement(info, "scoreboard-freeze-length").text = self.exam_info.get("freeze_duration", "1:00:00") # 封榜时间 自定义设置
    #     ET.SubElement(info, "contest-id").text = self.exam_info.get("id", "default-id")
    def _process_exam_info(self):
        """处理考试基础信息"""
        # url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/exams' 为学生端接口
        url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}'
        resp = self.session.get(url)
        self.exam_info = resp.json()

        info = ET.SubElement(self.contest_root, "info")
        problem_set = self.exam_info.get("problemSet", {})

        # 时间处理
        start_at = problem_set.get("startAt", "2025-05-16T00:00:00Z")
        start_time = datetime.fromisoformat(start_at.replace('Z', '+00:00')).timestamp()

        # 持续时间处理（从秒转换为时:分:秒格式）
        duration_seconds = problem_set.get("duration", 14400)  # 获取持续时间（秒）
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        # 添加子节点
        ET.SubElement(info, "length").text = duration_str
        ET.SubElement(info, "penalty").text = str(20)  # 罚时自定义设置，默认20分钟
        ET.SubElement(info, "started").text = "False"
        ET.SubElement(info, "starttime").text = f"{start_time:.1f}"
        ET.SubElement(info, "title").text = problem_set.get("name", "默认比赛")
        ET.SubElement(info, "short-title").text = problem_set.get("name", "Default Contest")
        ET.SubElement(info, "scoreboard-freeze-length").text = "1:00:00"  # 封榜时间自定义设置，默认1小时
        ET.SubElement(info, "contest-id").text = str(problem_set.get("id", "default-id"))
    def _add_static_nodes(self):
        """添加静态配置节点"""
        # 地区信息
        region = ET.SubElement(self.contest_root, "region")
        ET.SubElement(region, "external-id").text = "1"
        ET.SubElement(region, "name").text = "HBUE"

        # 判罚类型
        judgements = [
            {"id": "1", "acronym": "ACCEPTED", "name": "ACCEPTED", "solved": "true", "penalty": "false"},
            {"id": "2", "acronym": "SEGMENTATION_FAULT", "name": "SEGMENTATION_FAULT", "solved": "false","penalty": "true"},
            {"id": "3", "acronym": "WRONG_ANSWER", "name": "WRONG_ANSWER", "solved": "false", "penalty": "true"},
            {"id": "4", "acronym": "TIME_LIMIT_EXCEEDED", "name": "TIME_LIMIT_EXCEEDED", "solved": "false","penalty": "true"},
            {"id": "5", "acronym": "COMPILE_ERROR", "name": "COMPILE_ERROR", "solved": "false", "penalty": "false"},
            {"id": "6", "acronym": "FLOAT_POINT_EXCEPTION", "name": "FLOAT_POINT_EXCEPTION", "solved": "false","penalty": "true"},
            {"id": "7", "acronym": "MEMORY_LIMIT_EXCEEDED", "name": "MEMORY_LIMIT_EXCEEDED", "solved": "false","penalty": "true"},
            {"id": "8", "acronym": "NON_ZERO_EXIT_CODE", "name": "NON_ZERO_EXIT_CODE", "solved": "false","penalty": "true"},
            {"id": "9", "acronym": "RUNTIME_ERROR", "name": "RUNTIME_ERROR", "solved": "false", "penalty": "true"},
            {"id": "10", "acronym": "PRESENTATION_ERROR", "name": "PRESENTATION_ERROR", "solved": "false","penalty": "true"},
            {"id": "11", "acronym": "OUTPUT_LIMIT_EXCEEDED", "name": "OUTPUT_LIMIT_EXCEEDED", "solved": "false","penalty": "true"}
        ]
        for j in judgements:
            judgement = ET.SubElement(self.contest_root, "judgement")
            for key, value in j.items():
                ET.SubElement(judgement, key).text = str(value)

        # 编程语言
        languages = [("1", "c"), ("2", "c++"), ("3", "java"), ("4", "python")]
        for lang_id, lang_name in languages:
            lang = ET.SubElement(self.contest_root, "language")
            ET.SubElement(lang, "id").text = lang_id
            ET.SubElement(lang, "name").text = lang_name

    def _process_problems(self):
        """处理题目数据"""
        url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/preview/problems?problem_type=PROGRAMMING&page=0&limit=500'
        resp = self.session.get(url)
        problem_data = resp.json()
        problems = problem_data.get("problemSetProblems", [])
        letters = self.generate_letters(len(problems))

        # 创建题目映射表
        self.label_map = {
            p["id"]: {
                "xml_id": str(idx + 1),
                "letter": letters[idx]
            } for idx, p in enumerate(problems)
        }

        # 添加problem节点
        for idx, problem in enumerate(problems):
            problem_elem = ET.SubElement(self.contest_root, "problem")
            ET.SubElement(problem_elem, "id").text = str(idx + 1)
            ET.SubElement(problem_elem, "letter").text = letters[idx]
            ET.SubElement(problem_elem, "name").text = letters[idx]

    def _process_teams(self):
        """处理团队信息"""
        url = f'https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/members?limit=1000'
        resp = self.session.get(url)
        members_data = resp.json()

        for member in members_data.get("members", []):
            user_id = member.get("userId")
            student_info = members_data.get("studentUserById", {}).get(member.get("studentUserId", ""), {})

            team = ET.SubElement(self.contest_root, "team")
            ET.SubElement(team, "id").text = user_id
            ET.SubElement(team, "external-id").text = "1"
            ET.SubElement(team, "region").text = "HBUE"
            ET.SubElement(team, "name").text = student_info.get("name", "未知队员")
            ET.SubElement(team, "university").text = "HBUE"

    def _process_submissions(self):
        """处理提交记录"""
        submission_counter = 1
        base_url = f"https://pintia.cn/api/problem-sets/{self.selected_problem_set_id}/submissions"
        before = None

        # 获取比赛开始时间
        start_at = self.exam_info.get("problemSet", {}).get("startAt")
        contest_start = datetime.fromisoformat(start_at.replace('Z', '+00:00')).astimezone(timezone.utc)

        while True:
            url = f"{base_url}?limit=50" + (f"&before={before}" if before else "")
            resp = self.session.get(url)
            print(resp.status_code)
            if resp.status_code != 200:
                break

            data = resp.json()
            submissions = data.get("submissions", [])
            if not submissions:
                break

            for sub in submissions:
                self._add_submission_node(sub, submission_counter, contest_start)
                submission_counter += 1

            if not data.get("hasBefore", True):
                break
            before = list(data.get("showDetailBySubmissionId", {}).keys())[-1] if data.get(
                "showDetailBySubmissionId") else None

    def _add_submission_node(self, submission, counter, contest_start):
        """添加单个提交节点"""
        run = ET.SubElement(self.contest_root, "run")
        problem_id = submission["problemSetProblemId"]
        problem_info = self.label_map.get(problem_id, {"xml_id": "0"})

        # 时间计算
        submit_time = datetime.fromisoformat(submission["submitAt"].replace("Z", "+00:00")).astimezone(timezone.utc)
        time_diff = submit_time - contest_start

        # 节点内容
        elements = {
            "id": str(counter),
            "judged": "True",
            "language": "c",
            "problem": problem_info["xml_id"],
            "status": "done",
            "team": submission["userId"],
            "time": str(int(time_diff.total_seconds())),
            "timestamp": f"{submit_time.timestamp():.2f}",
            "solved": "true" if submission["status"] == "ACCEPTED" else "false",
            "penalty": "false" if submission["status"] == "COMPILE_ERROR" else "true",
            "result": submission["status"]
        }

        for key, value in elements.items():
            ET.SubElement(run, key).text = value

    def _add_finalized_node(self):
        """添加finalized节点"""
        finalized = ET.SubElement(self.contest_root, "finalized")
        ET.SubElement(finalized, "last_gold").text = "1"
        ET.SubElement(finalized, "last_silver").text = "1"
        ET.SubElement(finalized, "last_bronze").text = "1"
        ET.SubElement(finalized, "time").text = "0"

        # 计算结束时间
        duration = self.exam_info.get("duration", "4:00:00")
        hours, minutes, seconds = map(float, duration.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        end_timestamp = datetime.fromisoformat(
            self.exam_info.get("problemSet", {}).get("startAt").replace('Z', '+00:00')
        ).timestamp() + total_seconds

        ET.SubElement(finalized, "timestamp").text = f"{end_timestamp:.1f}"

    def _save_xml(self, path):
        """保存XML文件"""
        self.indent(self.contest_root)
        xml_str = ET.tostring(self.contest_root, encoding="unicode")
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(xml_str)


# 使用示例
if __name__ == "__main__":
    generator = PTAContestGenerator()

    # 获取题目集列表
    print("可用题目集：")
    for ps in generator.get_problem_sets():
        print(f"{ps['name']} ({ps['id']})")

    # 选择题目集（示例ID）
    generator.select_problem_set("1")

    # 生成XML文件
    output = generator.generate_contest_xml()
    print(f"生成完成：{output}")