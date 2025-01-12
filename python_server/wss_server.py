# python_server/wss_server.py

import asyncio
import websockets
import json
import os
import uuid
import subprocess

connected_clients = set()

async def handle_client(websocket):
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)

    try:
        async for message in websocket:
            data = json.loads(message)

            msg_type = data.get("type", "")
            if msg_type == "pose":
                # PoseデータをそのままUnityへブロードキャスト
                await broadcast(message, sender=websocket)
            elif msg_type == "pointcloud":
                # PointCloudデータを処理
                await handle_pointcloud(data, websocket)
            else:
                # その他のデータはブロードキャスト
                await broadcast(message, sender=websocket)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def broadcast(message, sender=None):
    # 送信元以外のクライアントへブロードキャスト
    for client in connected_clients:
        if client != sender:
            try:
                await client.send(message)
            except Exception as e:
                print(f"Failed to send to {client.remote_address}: {e}")

async def handle_pointcloud(data, websocket):
    points = data.get("points", [])
    frame_id = data.get("frame_id", 0)

    # 1. 点群データを一時テキストファイルに保存
    temp_txt = f"temp_{uuid.uuid4().hex}.txt"
    with open(temp_txt, "w") as f:
        for p in points:
            x, y, z = p
            f.write(f"{x} {y} {z}\n")

    # 2. Pythonスクリプトでメッシュ生成 (.ply)
    temp_ply = f"temp_{uuid.uuid4().hex}.ply"

    # ボクセルサイズなど必要に応じて調整
    voxel_size = 0.05

    # コマンドラインからスクリプトを呼び出す
    try:
        cmd = [
            "python", "convert_txt_to_ply_no_color.py",
            temp_txt, temp_ply, str(voxel_size)
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Mesh generation failed: {e}")
        # エラー発生時は一時ファイルを削除
        if os.path.exists(temp_txt):
            os.remove(temp_txt)
        return

    # 3. .ply を読み込み文字列化
    mesh_text = ""
    if os.path.exists(temp_ply):
        with open(temp_ply, "r") as plyf:
            mesh_text = plyf.read()
    else:
        print("PLY file not found.")
        # 一時ファイルを削除
        if os.path.exists(temp_txt):
            os.remove(temp_txt)
        return

    # 4. Unity向けに "mesh" タイプのJSONを作成
    mesh_json = {
        "type": "mesh",
        "frame_id": frame_id,
        "ply_data": mesh_text  # ASCII形式のplyファイル全文を格納
    }
    mesh_str = json.dumps(mesh_json)

    # Unityにブロードキャスト
    await broadcast(mesh_str, sender=websocket)

    # 後始末: 一時ファイルの削除
    if os.path.exists(temp_txt):
        os.remove(temp_txt)
    if os.path.exists(temp_ply):
        os.remove(temp_ply)

async def main():
    print("Starting WebSocket server on port 8003...")
    async with websockets.serve(handle_client, "0.0.0.0", 8083):
        await asyncio.Future()  # 永久に待機

if __name__ == "__main__":
    asyncio.run(main())
