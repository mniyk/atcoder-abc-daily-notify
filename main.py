import os

import requests
import sqlite3
from dotenv import load_dotenv


load_dotenv()

CONTESTS_URL = "https://kenkoooo.com/atcoder/resources/contests.json"
PROBLEMS_URL = "https://kenkoooo.com/atcoder/resources/problems.json"

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def init_db():
    con = sqlite3.connect("notified.db")
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS notified (contest_id TEXT PRIMARY KEY);")

    return con, cur


def select_contest_ids(cur):
    response = cur.execute("SELECT contest_id FROM notified;")

    contest_ids = [row[0] for row in response.fetchall()]

    return contest_ids


def insert_contest_id(cur, contest_id):
    cur.execute("INSERT INTO notified (contest_id) VALUES (?)", (contest_id,))


def get_abc_contests():
    contests = requests.get(CONTESTS_URL).json()
    abc_contests = [c for c in contests if c["id"].startswith("abc")]

    return abc_contests


def get_today_contest_id(contests, contest_ids):
    contest_id = None

    for c in reversed(contests):
        if c["id"] not in contest_ids:
            contest_id = c["id"]
            break

    return contest_id


def get_problems(contest_id: str):
    problems = requests.get(PROBLEMS_URL).json()
    problems = [p for p in problems if p["contest_id"] == contest_id]

    return problems


def filter_problem_index(problems, target: list[str]):
    problems = [p for p in problems if p["problem_index"] in target]

    return problems


def create_problem_info(problems):
    problem_info = [] 

    for p in problems:
        contest_id = p["contest_id"]
        problem_id = p["id"]
        problem_name = p["name"]

        problem_info.append({
            "name": problem_name,
            "url": f"https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}",
        })

    return problem_info


def create_send_text(problem_info):
    send_text = ""

    for p in problem_info:
        send_text += f"Name: {p['name']}\n"
        send_text += f"URL : {p['url']}\n\n"

    return send_text


def send_slack(send_text):
    requests.post(url=SLACK_WEBHOOK_URL, json={"text": send_text})


def main():
    con, cur = init_db()

    contest_ids = select_contest_ids(cur)

    abc_contests = get_abc_contests()
    contest_id = get_today_contest_id(abc_contests, contest_ids)
    problems = get_problems(contest_id)
    problems = filter_problem_index(problems, ["A", "B", "C"])
    problem_info = create_problem_info(problems)

    send_text = create_send_text(problem_info)
    send_slack(send_text)

    insert_contest_id(cur, contest_id)

    con.commit()

    cur.close()
    con.close()


if __name__ == "__main__":
    main()

