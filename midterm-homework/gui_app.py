"""東華校園美食情緒推薦系統（桌面完全版）
Desktop GUI App powered by CustomTkinter
國立東華大學 AI 課程作業專案
"""

import csv
import os
import random
import sys
import urllib.parse
import webbrowser
import customtkinter as ctk


class DataLoader:
    """美食資料庫讀取與標籤萃取模組"""

    def __init__(self, csv_filename="restaurants.csv"):
        # 取得腳本所在目錄之 CSV 完整路徑
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_dir, csv_filename)
        self.restaurants = []
        self.mood_tags = []
        self.weather_tags = []
        self.load_data()

    def load_data(self):
        """讀取 CSV 並動態萃取獨立心情與天氣標籤"""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"找不到美食資料庫檔案：{self.csv_path}")

        # 使用 utf-8-sig 防止 Windows BOM 字元干擾
        with open(self.csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self.restaurants = [row for row in reader if row.get("name")]

        moods_set = set()
        weathers_set = set()

        for r in self.restaurants:
            # 心情以 '/' 分割為獨立情緒標籤
            raw_mood = r.get("mood", "")
            for m in raw_mood.split("/"):
                m_clean = m.strip()
                if m_clean:
                    moods_set.add(m_clean)

            # 天氣標籤萃取（支援 CSV 獨立天氣情境）
            raw_weather = r.get("weather", "").strip()
            if raw_weather:
                weathers_set.add(raw_weather)

        # 排序心情標籤
        self.mood_tags = sorted(list(moods_set))

        # 天氣標籤依照常見邏輯排序（出大太陽 -> 陰天/涼爽 -> 下大雨）
        preferred_order = ["出大太陽", "陰天/涼爽", "下大雨"]
        self.weather_tags = [w for w in preferred_order if w in weathers_set]
        # 加入其他未在偏好順序內的天氣（若有）
        for w in sorted(list(weathers_set)):
            if w not in self.weather_tags:
                self.weather_tags.append(w)


class DongHwaFoodApp(ctk.CTk):
    """東華校園美食情緒推薦系統主視窗"""

    def __init__(self):
        super().__init__()

        # 設定深色模式與預設藍色主題
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 視窗基本設定
        self.title("東華校園美食情緒推薦系統（桌面完全版）🎓🍱")
        self.geometry("820x880")
        self.minsize(760, 800)

        # 載入資料庫
        self.data_loader = DataLoader()

        # 狀態追蹤變數
        self.current_mode = None  # "recommend" 或 "blind_box"
        self.last_selected_mood = None
        self.last_selected_weather = None
        self.cards_content_frame = None

        # 建立 UI 佈局
        self._build_header()
        self._build_controls()
        self._build_card_container()

        # 顯示初始歡迎介面
        self._show_welcome_card()

    def _build_header(self):
        """建立頂部標題區域"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🍱 東華校園美食情緒推薦系統",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=26, weight="bold"),
            text_color="#38ef7d",
        )
        title_label.pack(anchor="center")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="國立東華大學 ╳ 志學街 ╳ 校內各館 50 家精選美食智慧導航",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            text_color="#a0aab2",
        )
        subtitle_label.pack(anchor="center", pady=(4, 0))

    def _build_controls(self):
        """建立控制選單與按鈕區域"""
        controls_frame = ctk.CTkFrame(
            self,
            fg_color="#1e222d",
            corner_radius=14,
            border_width=1,
            border_color="#2e384d",
        )
        controls_frame.pack(fill="x", padx=25, pady=(5, 12))

        # 下拉選單橫排容器
        select_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        select_row.pack(fill="x", padx=20, pady=(15, 10))
        select_row.grid_columnconfigure((0, 1), weight=1)

        # 1. 心情選單
        mood_container = ctk.CTkFrame(select_row, fg_color="transparent")
        mood_container.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        mood_label = ctk.CTkLabel(
            mood_container,
            text="💭 現在的心情 (Mood)：",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13, weight="bold"),
            text_color="#e0e6ed",
        )
        mood_label.pack(anchor="w", pady=(0, 5))

        default_mood = self.data_loader.mood_tags[0] if self.data_loader.mood_tags else "追求高CP值"
        if "追求高CP值" in self.data_loader.mood_tags:
            default_mood = "追求高CP值"

        self.mood_combo = ctk.CTkComboBox(
            mood_container,
            values=self.data_loader.mood_tags,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            dropdown_font=ctk.CTkFont(family="Microsoft JhengHei UI", size=12),
            height=36,
            corner_radius=8,
            border_color="#3e4a61",
            button_color="#2980b9",
            button_hover_color="#3498db",
        )
        self.mood_combo.set(default_mood)
        self.mood_combo.pack(fill="x")

        # 2. 天氣選單
        weather_container = ctk.CTkFrame(select_row, fg_color="transparent")
        weather_container.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        weather_label = ctk.CTkLabel(
            weather_container,
            text="🌦️ 花蓮今天的天氣 (Weather)：",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13, weight="bold"),
            text_color="#e0e6ed",
        )
        weather_label.pack(anchor="w", pady=(0, 5))

        default_weather = self.data_loader.weather_tags[0] if self.data_loader.weather_tags else "出大太陽"
        self.weather_combo = ctk.CTkComboBox(
            weather_container,
            values=self.data_loader.weather_tags,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            dropdown_font=ctk.CTkFont(family="Microsoft JhengHei UI", size=12),
            height=36,
            corner_radius=8,
            border_color="#3e4a61",
            button_color="#2980b9",
            button_hover_color="#3498db",
        )
        self.weather_combo.set(default_weather)
        self.weather_combo.pack(fill="x")

        # 主要操作按鈕橫排
        btn_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 8))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        # 藍色推薦按鈕
        self.recommend_btn = ctk.CTkButton(
            btn_row,
            text="幫我推薦今天的東華美食！🚀",
            command=self.on_recommend_click,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=14, weight="bold"),
            height=42,
            corner_radius=8,
            fg_color="#1f538d",
            hover_color="#14375e",
        )
        self.recommend_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        # 紅色命運盲盒按鈕
        self.blind_box_btn = ctk.CTkButton(
            btn_row,
            text="命運盲盒抽籤！🎲",
            command=self.on_blind_box_click,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=14, weight="bold"),
            height=42,
            corner_radius=8,
            fg_color="#c0392b",
            hover_color="#962d22",
        )
        self.blind_box_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # 次要按鈕：「再換一組看看 🔄」
        self.reroll_btn = ctk.CTkButton(
            controls_frame,
            text="再換一組看看 🔄",
            command=self.on_reroll_click,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            height=34,
            corner_radius=8,
            fg_color="#2c3e50",
            hover_color="#34495e",
            text_color="#bdc3c7",
            state="disabled",  # 初始無推薦時停用
        )
        self.reroll_btn.pack(fill="x", padx=20, pady=(0, 12))

    def _build_card_container(self):
        """建立卡片動態渲染容器區塊 (CTkScrollableFrame)"""
        self.cards_scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=10,
        )
        self.cards_scrollable_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 15)
        )

    def _clear_cards_container(self):
        """精確銷毀舊的 Frame 容器，徹底避免 CustomTkinter 佈局殘留與閃爍問題"""
        if self.cards_content_frame is not None:
            self.cards_content_frame.destroy()
            self.cards_content_frame = None

        # 銷毀滾動容器中所有舊子元件
        for child in self.cards_scrollable_frame.winfo_children():
            child.destroy()

        # 重新建立乾淨的內容容器
        self.cards_content_frame = ctk.CTkFrame(
            self.cards_scrollable_frame, fg_color="transparent"
        )
        self.cards_content_frame.pack(fill="both", expand=True, padx=2, pady=2)

    def _show_welcome_card(self):
        """初始介面歡迎卡片"""
        self._clear_cards_container()

        welcome_frame = ctk.CTkFrame(
            self.cards_content_frame,
            fg_color="#181c24",
            corner_radius=14,
            border_width=1,
            border_color="#2e384d",
        )
        welcome_frame.pack(fill="both", expand=True, padx=10, pady=30)

        welcome_icon = ctk.CTkLabel(
            welcome_frame,
            text="🎓 🍽️ 🌲",
            font=ctk.CTkFont(size=42),
        )
        welcome_icon.pack(pady=(40, 10))

        title = ctk.CTkLabel(
            welcome_frame,
            text="歡迎來到東華校園美食推薦系統！",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=20, weight="bold"),
            text_color="#38ef7d",
        )
        title.pack(pady=(0, 10))

        info_text = (
            "「今天午餐吃什麼？」是每一位東華人共同的靈魂拷問。\n\n"
            "✨ 智慧推薦：選擇您目前的心情與花蓮今天的天氣，為您量身隨選 3 間最搭的美味餐廳！\n"
            "🎲 命運盲盒：完全不做選擇，讓命運之神直接為您隨機抽出 1 家店！\n"
            "🌧️ 貼心彩蛋：下大雨時系統會自動提醒您最溫暖安全的校內美食備案。\n"
            "🗺️ 導航整合：點擊任一推薦卡片即可一鍵開啟 Google Maps 專屬導航！"
        )
        desc = ctk.CTkLabel(
            welcome_frame,
            text=info_text,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            text_color="#c2c9d6",
            justify="left",
            wraplength=620,
        )
        desc.pack(padx=30, pady=(10, 40))

    def on_recommend_click(self):
        """功能一：智慧推薦按鈕點擊事件"""
        mood = self.mood_combo.get().strip()
        weather = self.weather_combo.get().strip()

        self.current_mode = "recommend"
        self.last_selected_mood = mood
        self.last_selected_weather = weather
        self.reroll_btn.configure(state="normal")

        self._render_recommendation(mood, weather)

    def on_blind_box_click(self):
        """功能二：命運盲盒抽籤點擊事件"""
        self.current_mode = "blind_box"
        self.reroll_btn.configure(state="normal")
        self._render_blind_box()

    def on_reroll_click(self):
        """功能三：再換一組看看點擊事件"""
        if self.current_mode == "recommend":
            mood = self.last_selected_mood or self.mood_combo.get().strip()
            weather = self.last_selected_weather or self.weather_combo.get().strip()
            self._render_recommendation(mood, weather)
        elif self.current_mode == "blind_box":
            self._render_blind_box()

    def _render_recommendation(self, mood, weather):
        """執行條件過濾與推薦卡片繪製"""
        self._clear_cards_container()

        # 下雨天彩蛋：若天氣為「下大雨」，在最頂部插入高亮提示框
        if weather == "下大雨":
            self._render_rainy_day_easter_egg()

        # 過濾符合店家
        matched = []
        for r in self.data_loader.restaurants:
            r_mood = r.get("mood", "")
            r_weather = r.get("weather", "")

            # 心情匹配（支援獨立標籤分割比對）
            mood_tokens = [m.strip() for m in r_mood.split("/")]
            mood_match = (mood in mood_tokens) or (mood in r_mood)

            # 天氣匹配
            weather_tokens = [w.strip() for w in r_weather.split("/")]
            weather_match = (weather in weather_tokens) or (weather in r_weather)

            if mood_match and weather_match:
                matched.append(r)

        # 推薦標題提示
        summary_label = ctk.CTkLabel(
            self.cards_content_frame,
            text=f"✨ 根據【{mood}】與【{weather}】為你推薦以下美食（共找到 {len(matched)} 家）：",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=14, weight="bold"),
            text_color="#70a1ff",
            anchor="w",
        )
        summary_label.pack(fill="x", padx=10, pady=(6, 10))

        if not matched:
            # 無符合店家時的友善提示
            empty_frame = ctk.CTkFrame(
                self.cards_content_frame,
                fg_color="#1e222d",
                corner_radius=12,
            )
            empty_frame.pack(fill="x", padx=10, pady=20)

            empty_text = ctk.CTkLabel(
                empty_frame,
                text="🔍 目前沒有找到完全吻合此心情與天氣組合的店家！\n建議換個心情標籤，或直接點擊「命運盲盒抽籤！🎲」交給命運決定～",
                font=ctk.CTkFont(family="Microsoft JhengHei UI", size=14),
                text_color="#e74c3c",
                justify="center",
            )
            empty_text.pack(padx=20, pady=30)
            return

        # 若超過 3 家，隨機隨選 (shuffle / sample) 3 家
        selected = random.sample(matched, min(3, len(matched)))

        for idx, restaurant in enumerate(selected, 1):
            self._render_restaurant_card(restaurant, rank=idx)

    def _render_blind_box(self):
        """執行命運盲盒隨機抽選與單一店家高亮繪製"""
        self._clear_cards_container()

        if not self.data_loader.restaurants:
            return

        # 從 50 家店中隨機抽選「僅限 1 家」
        chosen = random.choice(self.data_loader.restaurants)

        # 盲盒專屬高亮標題
        banner_frame = ctk.CTkFrame(
            self.cards_content_frame,
            fg_color="#3a2505",
            border_width=2,
            border_color="#f39c12",
            corner_radius=12,
        )
        banner_frame.pack(fill="x", padx=10, pady=(5, 12))

        blind_title = ctk.CTkLabel(
            banner_frame,
            text="🎉 命運之神今天推薦你吃：",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=18, weight="bold"),
            text_color="#f1c40f",
        )
        blind_title.pack(padx=15, pady=12)

        # 繪製高亮卡片
        self._render_restaurant_card(chosen, is_blind_box=True)

    def _render_rainy_day_easter_egg(self):
        """下雨天貼心彩蛋高亮提示"""
        easter_egg_frame = ctk.CTkFrame(
            self.cards_content_frame,
            fg_color="#102a43",
            border_width=2,
            border_color="#38bdf8",
            corner_radius=12,
        )
        easter_egg_frame.pack(fill="x", padx=10, pady=(5, 12))

        egg_label = ctk.CTkLabel(
            easter_egg_frame,
            text="🌧️ 花蓮大雨無情，系統已為你特別關注校內學餐！如果懶得出校門，留在多容館、集賢館或湖畔吃最溫暖安全喔！",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13, weight="bold"),
            text_color="#7dd3fc",
            wraplength=680,
            justify="left",
        )
        egg_label.pack(padx=15, pady=12)

    def _render_restaurant_card(self, r, rank=None, is_blind_box=False):
        """繪製單一餐廳推薦卡片"""
        # 卡片框線與背景
        border_color = "#f39c12" if is_blind_box else "#2e384d"
        border_width = 2 if is_blind_box else 1
        bg_color = "#202533" if is_blind_box else "#191d26"

        card = ctk.CTkFrame(
            self.cards_content_frame,
            fg_color=bg_color,
            corner_radius=12,
            border_width=border_width,
            border_color=border_color,
        )
        card.pack(fill="x", padx=10, pady=8)

        # 頂部列：店名與徽章
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 6))

        prefix = f"#{rank} " if rank else "🌟 "
        name_text = f"{prefix}{r.get('name', '未知店家')}"
        name_label = ctk.CTkLabel(
            top_row,
            text=name_text,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=18, weight="bold"),
            text_color="#f1c40f" if is_blind_box else "#ffffff",
        )
        name_label.pack(side="left")

        # 標籤列（類型、地點、價位）
        badges_row = ctk.CTkFrame(card, fg_color="transparent")
        badges_row.pack(fill="x", padx=16, pady=(0, 8))

        type_badge = ctk.CTkLabel(
            badges_row,
            text=f" 🍴 {r.get('type', '')} ",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=11, weight="bold"),
            fg_color="#2b394e",
            corner_radius=6,
            text_color="#93c5fd",
        )
        type_badge.pack(side="left", padx=(0, 6))

        loc_badge = ctk.CTkLabel(
            badges_row,
            text=f" 📍 {r.get('location', '')} ",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=11, weight="bold"),
            fg_color="#1f3d36",
            corner_radius=6,
            text_color="#6ee7b7",
        )
        loc_badge.pack(side="left", padx=(0, 6))

        price_badge = ctk.CTkLabel(
            badges_row,
            text=f" 💰 價位: {r.get('price', '')} ",
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=11, weight="bold"),
            fg_color="#452a20",
            corner_radius=6,
            text_color="#fdba74",
        )
        price_badge.pack(side="left")

        # 特色描述
        desc_label = ctk.CTkLabel(
            card,
            text=r.get("description", ""),
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=13),
            text_color="#cbd5e1",
            justify="left",
            wraplength=680,
        )
        desc_label.pack(fill="x", padx=16, pady=(0, 10))

        # 底部列：心情/天氣標籤備註 + Google Maps 導航按鈕
        bottom_row = ctk.CTkFrame(card, fg_color="transparent")
        bottom_row.pack(fill="x", padx=16, pady=(0, 14))

        meta_text = f"💭 {r.get('mood', '')}  |  🌦️ {r.get('weather', '')}"
        meta_label = ctk.CTkLabel(
            bottom_row,
            text=meta_text,
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=11),
            text_color="#8892b0",
        )
        meta_label.pack(side="left", anchor="w")

        # Google Maps 導航按鈕
        restaurant_name = r.get("name", "")
        restaurant_loc = r.get("location", "")
        map_btn = ctk.CTkButton(
            bottom_row,
            text="🗺️ 開啟 Google Maps 導航",
            command=lambda n=restaurant_name, loc=restaurant_loc: self.open_google_maps(n, loc),
            font=ctk.CTkFont(family="Microsoft JhengHei UI", size=12, weight="bold"),
            fg_color="#1a73e8",
            hover_color="#1558b0",
            height=32,
            corner_radius=6,
            width=165,
        )
        map_btn.pack(side="right")

    def open_google_maps(self, restaurant_name: str, location: str = ""):
        """
        整合 Google Maps 導航：
        若店家名稱或地點包含「校內」或「湖畔、集賢館、多容館、管院、管理學院」，搜尋詞加上「東華大學」
        其餘店家（志學街/前門）搜尋詞加上「花蓮壽豐」
        """
        campus_keywords = ["校內", "湖畔", "集賢館", "多容館", "管院", "管理學院"]
        is_campus = any(kw in restaurant_name or kw in location for kw in campus_keywords)

        suffix = "東華大學" if is_campus else "花蓮壽豐"
        search_query = f"{restaurant_name} {suffix}"
        encoded_query = urllib.parse.quote_plus(search_query)

        # 採用標準 Google Maps 搜尋導航路由
        url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        webbrowser.open_new_tab(url)


if __name__ == "__main__":
    try:
        app = DongHwaFoodApp()
        app.mainloop()
    except Exception as e:
        import traceback
        import tkinter.messagebox as messagebox
        err_msg = traceback.format_exc()
        try:
            with open("crash_report.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        messagebox.showerror("程式啟動錯誤", f"發生未預期的錯誤：\n\n{err_msg}")

