# python_server/convert_txt_to_ply_no_color.py

import open3d as o3d
import numpy as np
import sys

def txt_to_ply_with_mesh_ascii_no_color(txt_file_path, ply_file_path, voxel_size=0.05):
    """
    .txtファイルから点群を読み込み、ボクセルダウンサンプリング、座標変換、
    Poisson Surface Reconstructionでメッシュを生成し、色データなしでASCII形式の.plyファイルとして保存する関数

    Parameters:
    - txt_file_path: str, 入力の.txtファイルパス
    - ply_file_path: str, 出力の.plyファイルパス
    - voxel_size: float, ボクセルダウンサンプリングのサイズ（デフォルト: 0.05）
    """
    # .txtファイルの読み込み
    try:
        points = np.loadtxt(txt_file_path)
        if points.shape[1] < 3:
            raise ValueError("点群データには少なくとも3つの座標値が必要です。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return

    # Open3Dの点群オブジェクトを作成
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points[:, :3])  # 最初の3列を座標として使用

    # ボクセルダウンサンプリングを適用（オプション）
    if voxel_size > 0:
        print(f"ボクセルサイズ {voxel_size} でダウンサンプリングを実行中...")
        pcd = pcd.voxel_down_sample(voxel_size=voxel_size)
        print(f"ダウンサンプリング後の点数: {len(pcd.points)}")

    # 法線の推定（メッシュ生成には法線が必要）
    print("法線の推定を実行中...")
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

    # 座標変換：Y軸の符号を反転し、X軸回りに90度回転
    print("座標変換を適用中...")
    # Y軸反転
    y_invert_matrix = np.diag([1, -1, 1, 1])
    pcd.transform(y_invert_matrix)
    # X軸回りに90度回転
    rotation_matrix = pcd.get_rotation_matrix_from_axis_angle([np.pi / 2, 0, 0])  # 90度をラジアンに変換
    pcd.rotate(rotation_matrix, center=(0, 0, 0))

    # Poisson Surface Reconstructionによるメッシュ生成
    print("Poisson Surface Reconstructionを実行中...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
    print("メッシュ生成完了。")

    # メッシュをフィルタリング（不要な部分を除去）
    print("メッシュをボクセル領域にクロップ中...")
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)

    # 色データを除去（存在する場合）
    if mesh.has_vertex_colors():
        print("メッシュから色データを除去中...")
        mesh.vertex_colors = o3d.utility.Vector3dVector([])

    # メッシュをASCII形式で保存（色データを含めない）
    print(f"ASCII形式のメッシュ.plyファイルを保存しています: {ply_file_path}")
    o3d.io.write_triangle_mesh(ply_file_path, mesh, write_ascii=True, write_vertex_normals=True, write_vertex_colors=False)
    print("PLYファイルの保存が完了しました。")

if __name__ == "__main__":
    # コマンドライン引数:
    #   python convert_txt_to_ply_no_color.py <input_txt> <output_ply> [voxel_size]
    if len(sys.argv) < 3:
        print("Usage: python convert_txt_to_ply_no_color.py <input_txt> <output_ply> [voxel_size]")
        sys.exit(1)
    input_txt = sys.argv[1]
    output_ply = sys.argv[2]
    voxel_size = 0.05
    if len(sys.argv) >= 4:
        voxel_size = float(sys.argv[3])

    txt_to_ply_with_mesh_ascii_no_color(input_txt, output_ply, voxel_size=voxel_size)
