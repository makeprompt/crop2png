import os
from tkinter import Tk, Canvas, filedialog, Label, Button
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import re

class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Cropper")

        # UI要素
        self.label = Label(root, text="画像またはフォルダをドラッグ＆ドロップしてください。マウスホイールで画像切り替え、sで選択範囲を保存、aで画像全体を保存します。")
        self.label.pack()

        # self.open_button = Button(root, text="画像を選択", command=self.open_image)
        # self.open_button.pack()

        self.canvas = Canvas(root, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        # self.crop_button = Button(root, text="トリミングを保存(s)", command=self.save_crop, state="disabled")
        # self.crop_button.pack()

        # 初期化
        self.image = None
        self.tk_image = None
        self.start_x = self.start_y = 0
        self.rect = None
        self.crop_coords = None
        self.scale = 1  # 表示倍率
        self.image_files = []  # フォルダ内の画像ファイルリスト
        self.current_image_index = -1  # 現在表示している画像のインデックス
        self.folder_path = ""  # 現在のフォルダパス

        # ウィンドウのサイズを取得
        self.window_width = 1200
        self.window_height = 800
        self.ui_reserved_height = 25  # ラベルやボタンの高さの合計

        # キーボードイベントのバインド
        self.root.bind("s", lambda event: self.save_crop())
        self.root.bind("a", lambda event: self.save_image())
        # ドラッグ＆ドロップの設定
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)


    
    def on_drop(self, event):
        # ドラッグ＆ドロップされたファイルorフォルダを読み込む
        # Windows形式で追加される{}を削除してリスト化

        file_path = self.parse_file_paths(event.data)

        # print(file_path) #デバックprint

        # if file_path.startswith("{") and file_path.endswith("}"):
        #     file_path = re.findall(r'\{(.*?)\}',file_path)  # 非貪欲マッチ（最小マッチ）
        #     file_path.sort()
        # 複数ファイルがドラッグされた場合、ソートして最初の1つだけを処理
        if os.path.isfile(file_path[0]):
            self.load_dropped_file(file_path[0])
        
        if os.path.isdir(file_path[0]):
            self.load_dropped_folder(file_path[0])

    def parse_file_paths(self,data):

        # パスが{}で囲まれている場合を考慮
        pattern = r'(?<!\\)\"(.*?)\"|(?<!\\)\{(.*?)\}|(\S+)'  # ダブルクオート、波括弧、スペース区切り対応
        matches = re.findall(pattern, data)
        # マッチしたグループから値を抽出してリスト化
        return [match[0] or match[1] or match[2] for match in matches]

    def load_dropped_file(self, file_path):

        if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")):
            # 現在のフォルダパスを保存
            self.folder_path = os.path.dirname(file_path)

            # フォルダ内の画像ファイルをリスト化
            self.image_files = [
                f for f in os.listdir(self.folder_path)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"))
            ]
            self.image_files.sort()  # ファイル名でソート
            self.current_image_index = self.image_files.index(os.path.basename(file_path))

            self.load_image(os.path.join(self.folder_path, self.image_files[self.current_image_index]))

            # マウスホイールイベントをバインド
            self.root.bind("<MouseWheel>", self.scroll_image)

    def load_dropped_folder(self, file_path):
        # 現在のフォルダパスを保存
        self.folder_path = file_path

        # フォルダ内の画像ファイルをリスト化
        self.image_files = [
            f for f in os.listdir(self.folder_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"))
        ]
        self.image_files.sort()  # ファイル名でソート
        # 0枚目を開く
        self.load_image(os.path.join(self.folder_path, self.image_files[0]))

        # マウスホイールイベントをバインド
        self.root.bind("<MouseWheel>", self.scroll_image)

    def open_image(self):
        # ファイルダイアログから画像を選択
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif")]
        )
        if file_path:
            self.load_dropped_file(file_path)

    def load_image(self, file_path):
        # 画像を読み込んで表示
        self.image = Image.open(file_path)
        self.calculate_scale()
        self.display_image()

    def calculate_scale(self):
        # 画像を表示エリアに収めるための表示倍率を計算
        if self.image:
            img_width, img_height = self.image.size
            available_width = self.window_width
            available_height = self.window_height - self.ui_reserved_height  # UI領域を除外
            self.scale = min(available_width / img_width, available_height / img_height, 1)

    def display_image(self):
        if self.image:
            # 表示倍率を適用して縮小画像を作成
            display_width = int(self.image.width * self.scale)
            display_height = int(self.image.height * self.scale)
            resized_image = self.image.resize((display_width, display_height), Image.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_image)

            # Canvasに画像を描画
            self.canvas.config(width=display_width, height=display_height)
            self.canvas.delete("all")  # 前の画像を削除
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

            # マウスイベントをバインド
            self.canvas.bind("<ButtonPress-1>", self.start_crop)
            self.canvas.bind("<B1-Motion>", self.update_crop)
            self.canvas.bind("<ButtonRelease-1>", self.end_crop)

            # self.crop_button.config(state="normal")

    def scroll_image(self, event):
        # マウスホイールで前後の画像に移動
        if self.image_files:
            if event.delta > 0:  # ホイールを上に動かした場合
                self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            elif event.delta < 0:  # ホイールを下に動かした場合
                self.current_image_index = (self.current_image_index + 1) % len(self.image_files)

            # 新しい画像をロード
            new_image_path = os.path.join(self.folder_path, self.image_files[self.current_image_index])
            self.load_image(new_image_path)

    def start_crop(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
        )

    def update_crop(self, event):
        end_x, end_y = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, end_x, end_y)

    def end_crop(self, event):
        end_x, end_y = event.x, event.y

        # 座標の順序を正規化（左 < 右、上 < 下）
        x1, x2 = sorted((self.start_x, end_x))
        y1, y2 = sorted((self.start_y, end_y))

        # 選択範囲を元の画像座標系に変換
        self.crop_coords = (
            x1 / self.scale,
            y1 / self.scale,
            x2 / self.scale,
            y2 / self.scale,
        )


    def save_crop(self):
        if self.crop_coords and self.image:
            # 座標を取得してトリミング範囲を確定(範囲が画像サイズを超えた場合は画像サイズを最大とする)
            img_width, img_height = self.image.size            
            x1, y1, x2, y2 = map(int, self.crop_coords)
            x1, y1 = max(0, min(x1, img_width)), max(0, min(y1, img_height))
            x2, y2 = max(0, min(x2, img_width)), max(0, min(y2, img_height))

            # end_cropで順序はソートされているが念のため、再度範囲指定
            cropped_image = self.image.crop((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))) 


            # 保存フォルダの作成
            output_folder = os.path.join(os.getcwd(), "output")
            os.makedirs(output_folder, exist_ok=True)

            # 重複しないファイル名を生成(4桁0フィルで重複しない数値までチェックして保存)
            base_name = "crop"
            ext = ".png"
            counter = 1
            save_path = os.path.join(output_folder, f"{base_name}_{counter:04d}{ext}")
            while os.path.exists(save_path):
                counter += 1
                save_path = os.path.join(output_folder, f"{base_name}_{counter:04d}{ext}")

            # 画像を保存
            cropped_image.save(save_path)
            self.label.config(text=f"トリミングした画像を保存しました: {save_path}")
    def save_image(self):
        if self.image:

            # 保存フォルダの作成
            output_folder = os.path.join(os.getcwd(), "output")
            os.makedirs(output_folder, exist_ok=True)

            # 重複しないファイル名を生成(4桁0フィルで重複しない数値までチェックして保存)
            base_name = "crop"
            ext = ".png"
            counter = 1
            save_path = os.path.join(output_folder, f"{base_name}_{counter:04d}{ext}")
            while os.path.exists(save_path):
                counter += 1
                save_path = os.path.join(output_folder, f"{base_name}_{counter:04d}{ext}")

            # 画像を保存
            self.image.save(save_path)
            self.label.config(text=f"トリミングした画像を保存しました: {save_path}")
if __name__ == "__main__":
    root = TkinterDnD.Tk()  # TkinterDnDを使用
    root.geometry("1200x800")  # ウィンドウサイズを指定
    app = ImageCropperApp(root)
    root.mainloop()
