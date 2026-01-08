# app_fixed.py - 英文打字测试系统
from flask import Flask, render_template, request, jsonify, session
import random
import time
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'typing_test_secret_key_2024'

# 真实的数据存储文件
HISTORY_FILE = 'typing_history.json'
LEADERBOARD_FILE = 'typing_leaderboard.json'

# 确保数据文件存在
def ensure_data_files():
    for file_path in [HISTORY_FILE, LEADERBOARD_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"📁 创建数据文件: {file_path}")

# 英文样本文本库
SAMPLE_TEXTS = {
    "english": {
        "简单": [
            "The quick brown fox jumps over the lazy dog.",
            "Practice makes perfect when learning new skills.",
            "Time flies like an arrow, fruit flies like a banana.",
            "Hello world! This is a typing speed test.",
            "Coding is fun and challenging at the same time."
        ],
        "中等": [
            "Python programming language is widely used in data science and web development.",
            "Typing speed can be improved through consistent practice and proper techniques.",
            "Artificial intelligence is transforming many industries around the world.",
            "Learning to code opens up many career opportunities in the tech industry.",
            "The internet has revolutionized how we communicate and access information."
        ],
        "困难": [
            "Object-oriented programming emphasizes the use of objects that contain both data and behavior.",
            "Machine learning algorithms require careful feature engineering and hyperparameter tuning.",
            "Distributed systems must handle challenges like network latency and partial failures gracefully.",
            "Quantum computing leverages quantum mechanical phenomena to perform complex calculations.",
            "Natural language processing involves teaching computers to understand human languages."
        ]
    }
}

def calculate_wpm(typed_text, time_taken):
    """计算WPM（每分钟单词数）"""
    if time_taken == 0:
        return 0
    
    # 英文：按空格分隔单词
    words = len(typed_text.strip().split())
    wpm = (words / (time_taken / 60))
    return round(wpm, 1)

def calculate_accuracy(original, typed):
    """计算准确率"""
    if not typed:
        return 0
    
    # 按字符对比
    correct = 0
    min_len = min(len(original), len(typed))
    
    for i in range(min_len):
        if original[i] == typed[i]:
            correct += 1
    
    if len(original) == 0:
        return 0
    
    # 惩罚额外的字符
    extra_penalty = max(0, len(typed) - len(original)) * 0.5
    correct = max(0, correct - extra_penalty)
    
    accuracy = (correct / len(original)) * 100
    return round(max(0, min(100, accuracy)), 1)

def calculate_score(wpm, accuracy):
    """计算综合评分"""
    # WPM评分：60WPM为满分40分
    wpm_score = min(wpm / 60 * 40, 40)
    # 准确率评分：100%为满分60分
    accuracy_score = accuracy * 0.6
    
    score = wpm_score + accuracy_score
    return round(score, 1)

def get_grade(score):
    """根据评分获取等级"""
    if score >= 90:
        return "专业级"
    elif score >= 80:
        return "优秀"
    elif score >= 70:
        return "良好"
    elif score >= 60:
        return "及格"
    else:
        return "需要练习"

def load_history():
    """加载历史记录"""
    ensure_data_files()
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except Exception as e:
        print(f"加载历史记录错误: {e}")
        return []

def save_history(history):
    """保存历史记录"""
    try:
        if len(history) > 100:
            history = history[-100:]
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        return False

def load_leaderboard():
    """加载排行榜"""
    ensure_data_files()
    try:
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                print("排行榜数据不是列表格式，重置为空列表")
                return []
    except Exception as e:
        print(f"加载排行榜错误: {e}")
        return []

def save_leaderboard(leaderboard):
    """保存排行榜"""
    try:
        leaderboard.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        if len(leaderboard) > 50:
            leaderboard = leaderboard[:50]
        
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存排行榜失败: {e}")
        return False

def add_to_leaderboard(username, wpm, accuracy, score, difficulty):
    """添加到排行榜"""
    leaderboard = load_leaderboard()
    
    record = {
        'username': username,
        'wpm': wpm,
        'accuracy': accuracy,
        'score': score,
        'difficulty': difficulty,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    leaderboard.append(record)
    save_leaderboard(leaderboard)
    
    return leaderboard

def add_to_history(username, record):
    """添加到历史记录"""
    history = load_history()
    
    record['username'] = username
    history.append(record)
    save_history(history)
    
    return history

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/start_test', methods=['POST'])
def start_test():
    """开始测试"""
    try:
        data = request.json
        difficulty = data.get('difficulty', '中等')
        
        if difficulty in SAMPLE_TEXTS["english"]:
            text = random.choice(SAMPLE_TEXTS["english"][difficulty])
        else:
            text = random.choice(SAMPLE_TEXTS["english"]["中等"])
        
        session['test_text'] = text
        session['start_time'] = time.time()
        session['difficulty'] = difficulty
        
        return jsonify({
            'success': True,
            'text': text,
            'difficulty': difficulty
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit_test', methods=['POST'])
def submit_test():
    """提交测试结果"""
    try:
        data = request.json
        typed_text = data.get('text', '')
        username = data.get('username', '匿名用户')
        
        original_text = session.get('test_text', '')
        start_time = session.get('start_time', time.time())
        difficulty = session.get('difficulty', '中等')
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        wpm = calculate_wpm(typed_text, time_taken)
        accuracy = calculate_accuracy(original_text, typed_text)
        score = calculate_score(wpm, accuracy)
        grade = get_grade(score)
        
        record = {
            'original_text': original_text,
            'typed_text': typed_text,
            'wpm': wpm,
            'accuracy': accuracy,
            'score': score,
            'grade': grade,
            'time_taken': round(time_taken, 2),
            'difficulty': difficulty,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        add_to_history(username, record)
        add_to_leaderboard(username, wpm, accuracy, score, difficulty)
        
        session.pop('test_text', None)
        session.pop('start_time', None)
        
        return jsonify({
            'success': True,
            'result': record
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_leaderboard', methods=['GET'])
def get_leaderboard():
    """获取排行榜"""
    try:
        leaderboard = load_leaderboard()
        
        for record in leaderboard:
            username = record.get('username', '匿名用户')
            if len(username) > 15:
                record['display_name'] = username[:12] + '...'
            else:
                record['display_name'] = username
        
        leaderboard.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_20 = leaderboard[:20]
        
        return jsonify({
            'success': True,
            'leaderboard': top_20,
            'total': len(leaderboard)
        })
        
    except Exception as e:
        print(f"获取排行榜错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        history = load_history()
        leaderboard = load_leaderboard()
        
        total_tests = len(history)
        
        if total_tests > 0:
            avg_wpm = sum(h.get('wpm', 0) for h in history) / total_tests
            max_wpm = max((h.get('wpm', 0) for h in history), default=0)
            avg_accuracy = sum(h.get('accuracy', 0) for h in history) / total_tests
            
            difficulties = {}
            for h in history:
                diff = h.get('difficulty', '未知')
                difficulties[diff] = difficulties.get(diff, 0) + 1
        else:
            avg_wpm = 0
            max_wpm = 0
            avg_accuracy = 0
            difficulties = {}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_tests': total_tests,
                'avg_wpm': round(avg_wpm, 1),
                'max_wpm': round(max_wpm, 1),
                'avg_accuracy': round(avg_accuracy, 1),
                'difficulties': difficulties,
                'leaderboard_count': len(leaderboard)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🎮 英文打字速度测试系统")
    print("=" * 60)
    print("系统特点:")
    print("1. ✅ 英文打字速度测试")
    print("2. ✅ 专业简洁的界面")
    print("3. ✅ 实时排行榜系统")
    print("4. ✅ 数据持久化存储")
    print("=" * 60)
    
    ensure_data_files()
    
    for file_path in [HISTORY_FILE, LEADERBOARD_FILE]:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"📁 {file_path}: {size} 字节")
    
    print(f"🌐 访问地址: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
