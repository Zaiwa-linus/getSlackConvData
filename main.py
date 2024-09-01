import connector
import cacheLib
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import mainUtils
import logger
import sys

def main():
    # ディレクトリのチェックと作成
    if not mainUtils.checkAndCreateDirs():
        print("Required files (input.csv or token.csv) are missing in the input directory. Exiting...")
        sys.exit(1)  # プログラムを終了

    # 入力情報の取得
    df = mainUtils.getInputInfo()

    # 必要な列のチェック
    required_columns = {'id', 'requestDateRange'}
    if not required_columns.issubset(df.columns):
        print("The input file is missing required columns (id, requestDateRange). Exiting...")
        sys.exit(1)  # プログラムを終了

    # UserCacheインスタンスを作成
    user_cache = cacheLib.UserCache(valid_days=100)

    # SlackManagerインスタンスを作成
    manager = connector.SlackManager(user_cache)

    # Loggerインスタンスを作成
    lgr = logger.Logger()

    # 各チャンネルの処理
    for index, row in df.iterrows():
        channel_id = row.id
        get_thread_date_length = row.requestDateRange

        # チャネルのメンバーリストのチェックと取得
        if mainUtils.checkMemberList(channel_id):
            lgr.view_log(f"User list for channel {channel_id} already exists. Skipping user list retrieval.")
        else:
            lgr.view_log(f"Requesting user list for channel {channel_id}...")
            user_list = manager.get_all_user_info(channel_id)
            mainUtils.saveMemberList(channel_id, user_list)
            lgr.view_log(f"User list for channel {channel_id} saved successfully.")

        # チャネルのメッセージ履歴のチェックと取得
        if mainUtils.checkIsHasHistory(channel_id):
            lgr.view_log(f"Message history for channel {channel_id} already exists. Skipping message retrieval.")
        else:
            lgr.view_log(f"Requesting message list for channel {channel_id}...")
            message_list = manager.get_all_messages(channel_id, get_thread_date_length)
            lgr.view_log(f"Message list for channel {channel_id} retrieved successfully.")

            # メッセージ履歴の保存
            lgr.view_log(f"Saving message history for channel {channel_id}...")
            mainUtils.saveHistory(channel_id, message_list)
            lgr.view_log(f"Message history for channel {channel_id} saved successfully.")

            # リアクションデータの変換と保存
            lgr.view_log(f"Converting reactions for channel {channel_id}...")
            reaction_list = manager.convert_messages_to_react_data(message_list)
            lgr.view_log(f"Reactions converted for channel {channel_id}.")

            lgr.view_log(f"Saving reactions for channel {channel_id}...")
            mainUtils.saveReactions(channel_id, reaction_list)
            lgr.view_log(f"Reactions for channel {channel_id} saved successfully.")

if __name__ == "__main__":
    main()
