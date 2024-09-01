import os
import pandas as pd
from datetime import datetime

# グローバル変数の定義
BASE_DIRS = {
    "input": "input",
    "output": "output",
    "work": "work"
}
TODAY = datetime.now().strftime('%Y%m%d')
TODAY_DIR = os.path.join(BASE_DIRS["work"], TODAY)


def checkAndCreateDirs():
    """
    input, output, workのディレクトリを保有しているかチェックし、
    保有していない場合は新規作成する。
    workディレクトリに本日の日付のフォルダを作成する。
    inputディレクトリ内にinput.csvとtoken.csvを保有しているかをチェックする。

    :return: True if input.csv and token.csv exist, else False
    """
    # ディレクトリの存在確認と作成
    for dir_path in BASE_DIRS.values():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # workディレクトリ内に本日の日付のフォルダを作成
    if not os.path.exists(TODAY_DIR):
        os.makedirs(TODAY_DIR)

    # inputディレクトリ内にinput.csvとtoken.csvが存在するかをチェック
    input_files = ["input.csv", "token.csv"]
    return all(os.path.exists(os.path.join(BASE_DIRS["input"], file)) for file in input_files)


def getInputInfo():
    """
    input/input.csvフォルダの中身をpandaで読み取り、値を返す。

    :return: pandas DataFrame of input.csv
    """
    input_path = os.path.join(BASE_DIRS["input"], "input.csv")
    if os.path.exists(input_path):
        return pd.read_csv(input_path)
    else:
        raise FileNotFoundError(f"{input_path} not found.")


def checkMemberList(channel_id):
    """
    引数にチャネルのIDを受取、workディレクトリ内に、
    ファイルがあるかを確認、結果をboolで返す。

    :param channel_id: チャネルID
    :return: True if memberEmails file exists, else False
    """
    file_name = f"{channel_id}_{TODAY}_memberEmails.csv"
    return os.path.exists(os.path.join(TODAY_DIR, file_name))


def checkIsHasReactions(channel_id):
    """
    引数にチャネルのIDを受取、workディレクトリ内に、
    ファイルがあるかを確認、結果をboolで返す。

    :param channel_id: チャネルID
    :return: True if channelReactions file exists, else False
    """
    file_name = f"{channel_id}_{TODAY}_channelReactions.xlsx"
    return os.path.exists(os.path.join(TODAY_DIR, file_name))


def checkIsHasHistory(channel_id):
    """
    引数にチャネルのIDを受取、workディレクトリ内に、
    ファイルがあるかを確認、結果をboolで返す。

    :param channel_id: チャネルID
    :return: True if channelHistory file exists, else False
    """
    file_name = f"{channel_id}_{TODAY}_channelHistory.xlsx"
    return os.path.exists(os.path.join(TODAY_DIR, file_name))


def saveHistory(channel_id, df):
    """
    所定のファイル名でhistoryデータを保存する。

    :param channel_id: チャネルID
    :param df: 保存するデータフレーム
    """
    file_name = f"{channel_id}_{TODAY}_channelHistory.xlsx"
    df.to_excel(os.path.join(TODAY_DIR, file_name), index=False)


def saveReactions(channel_id, df):
    """
    所定のファイル名でリアクションデータを保存する。

    :param channel_id: チャネルID
    :param df: 保存するデータフレーム
    """
    file_name = f"{channel_id}_{TODAY}_channelReactions.xlsx"
    df.to_excel(os.path.join(TODAY_DIR, file_name), index=False)


def saveMemberList(channel_id, df):
    """
    所定のファイル名でメンバーリストを保存する。

    :param channel_id: チャネルID
    :param df: 保存するデータフレーム
    """
    file_name = f"{channel_id}_{TODAY}_memberEmails.csv"
    df.to_csv(os.path.join(TODAY_DIR, file_name), index=False)
