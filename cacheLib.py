import csv
import os
from datetime import datetime, timedelta


class UserCache:
    def __init__(self, valid_days: int):
        # 有効ログ期間を指定された日数に設定
        self.valid_period = timedelta(days=valid_days)
        self.cache_file = "cache.csv"
        self.users = []  # ローカルプロパティとしてユーザーデータを保持
        
        # CSVファイルの読み込みまたは新規作成
        if os.path.exists(self.cache_file):
            self._load_cache()
        else:
            self._create_cache_file()

    def _create_cache_file(self):
        # 新規のキャッシュファイルを作成
        with open(self.cache_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # ヘッダー行を書き込み
            writer.writerow(['user_id', 'email', 'last_updated'])

    def _load_cache(self):
        # CSVファイルを読み込み、ユーザー情報をローカルプロパティに格納
        with open(self.cache_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = {
                    'user_id': row['user_id'],
                    'email': row['email'],
                    'last_updated': datetime.strptime(row['last_updated'], '%Y-%m-%d %H:%M:%S')
                }
                self.users.append(user)

    @property
    def valid_users(self):
        # 有効期間内のユーザーのみをリストとして返す
        now = datetime.now()
        return [
            user for user in self.users
            if now - user['last_updated'] <= self.valid_period
        ]

    def add_user(self, user_id: str, email: str):
        # ユーザーを追加し、キャッシュファイルにも書き込む
        now = datetime.now()
        user = {
            'user_id': user_id,
            'email': email,
            'last_updated': now
        }
        self.users.append(user)
        self._write_to_cache(user)

    def _write_to_cache(self, user):
        # ユーザー情報をCSVファイルに追加
        with open(self.cache_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user['user_id'], user['email'], user['last_updated'].strftime('%Y-%m-%d %H:%M:%S')])



