from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.config import Config

# Early config – important for clean console & no artifacts on Hyprland / Intel iGPU
Config.set('input', 'mouse', 'mouse,disable_multitouch')           # no red/orange touch dots
Config.set('input', 'mtdev_%(name)s', 'disable')                   # stop mtdev spam
Config.set('input', 'probesysfs', 'disable')
Config.set('graphics', 'multisamples', '0')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

from tracker import load_portfolio, fetch_latest_nav

Window.size = (920, 720)
Window.clearcolor = (0.07, 0.07, 0.07, 1)

class PortfolioApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        title = Label(
            text='FundEngine Portfolio Tracker',
            size_hint_y=0.08,
            font_size=26,
            bold=True,
            color=(0.9, 0.9, 1, 1)
        )
        self.root.add_widget(title)

        scroll = ScrollView(size_hint=(1, 0.45))
        self.grid = GridLayout(cols=4, spacing=12, padding=8, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        self.root.add_widget(scroll)

        self.plot_widget = KivyImage(
            size_hint=(1, 0.35),
            allow_stretch=True,
            keep_ratio=True
        )
        self.root.add_widget(self.plot_widget)

        self.status_label = Label(
            text="Loading...",
            size_hint_y=0.05,
            font_size=16,
            color=(0.8, 1, 0.8, 1)
        )
        self.root.add_widget(self.status_label)

        btn_box = BoxLayout(size_hint_y=0.08, spacing=15)
        refresh_btn = Button(text='Refresh Data', size_hint_x=0.6, background_color=(0.2, 0.6, 1, 1))
        refresh_btn.bind(on_press=self.update_data)
        quit_btn = Button(text='Quit', size_hint_x=0.4, background_color=(0.9, 0.3, 0.3, 1))
        quit_btn.bind(on_press=lambda x: self.stop())
        btn_box.add_widget(refresh_btn)
        btn_box.add_widget(quit_btn)
        self.root.add_widget(btn_box)

        Clock.schedule_once(self.update_data, 0.1)
        return self.root

    def update_data(self, *args):
        self.grid.clear_widgets()
        self.status_label.text = "Fetching latest NAVs..."

        headers = ['Fund Name', 'NAV', 'Units', 'Value (₹)']
        for h in headers:
            self.grid.add_widget(Label(
                text=f"[b]{h}[/b]", markup=True,
                size_hint_y=None, height=45,
                bold=True, color=(0.9, 0.9, 1, 1)
            ))

        portfolio = load_portfolio()
        total_value = 0.0
        row_count = 0
        last_date = "unknown"

        for code, info in portfolio.items():
            nav, date = fetch_latest_nav(code)
            row_count += 1
            if nav is not None:
                if date:
                    last_date = date
                value = nav * info['units']
                total_value += value

                color = (1.0, 1.0, 1.0, 1.0) if row_count % 2 == 0 else (0.88, 0.92, 1.0, 1.0)

                self.grid.add_widget(Label(text=info['name'], size_hint_y=None, height=42, color=color))
                self.grid.add_widget(Label(text=f"{nav:.2f}", size_hint_y=None, height=42, color=color))
                self.grid.add_widget(Label(text=f"{info['units']:.2f}", size_hint_y=None, height=42, color=color))
                self.grid.add_widget(Label(text=f"{value:,.2f}", size_hint_y=None, height=42, color=color))
            else:
                self.grid.add_widget(Label(text=f"{info.get('name', code)} (failed)", size_hint_y=None, height=42, color=(1.0, 0.6, 0.6, 1.0)))
                self.grid.add_widget(Label(text="-", size_hint_y=None, height=42))
                self.grid.add_widget(Label(text="-", size_hint_y=None, height=42))
                self.grid.add_widget(Label(text="-", size_hint_y=None, height=42))

        # Total
        self.grid.add_widget(Label(text="[b]TOTAL[/b]", markup=True, size_hint_y=None, height=55, color=(0.9, 1.0, 0.6, 1.0)))
        self.grid.add_widget(Label(text="", size_hint_y=None, height=55))
        self.grid.add_widget(Label(text="", size_hint_y=None, height=55))
        self.grid.add_widget(Label(text=f"[b]{total_value:,.2f}[/b]", markup=True, size_hint_y=None, height=55, color=(0.9, 1.0, 0.6, 1.0)))

        proj_2y = total_value * (1.12 ** 2)
        proj_5y = total_value * (1.12 ** 5)
        self.status_label.text = (
            f"Last update: {last_date}   •   "
            f"2 years @12% ≈ ₹{proj_2y:,.0f}   •   "
            f"5 years @12% ≈ ₹{proj_5y:,.0f}"
        )

        self.update_plot(portfolio)

    def update_plot(self, portfolio):
        self.plot_widget.source = ''
        self.plot_widget.texture = None

        names = []
        values = []

        for code, info in portfolio.items():
            nav, _ = fetch_latest_nav(code)
            if nav is not None:
                display_name = info['name'][:16] + '…' if len(info['name']) > 16 else info['name']
                names.append(display_name)
                values.append(nav * info['units'])

        if not values:
            return

        fig, ax = plt.subplots(figsize=(7.4, 4.4), dpi=100)
        bars = ax.bar(names, values, color=['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'])
        ax.set_title('Portfolio Value Breakdown', fontsize=14, pad=12)
        ax.set_ylabel('Value (₹)', fontsize=11)
        ax.tick_params(axis='x', rotation=40, labelsize=9.5)
        ax.tick_params(axis='y', labelsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.35)

        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h,
                    f'₹{h:,.0f}', ha='center', va='bottom', fontsize=9)

        ax.set_ylim(0, max(values) * 1.18)
        plt.tight_layout()

        # ── Critical part: direct buffer + flip for Intel/Mesa ──
        fig.canvas.draw()
        buffer = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        buffer.shape = (fig.canvas.get_width_height()[::-1] + (4,))

        # ARGB → RGBA + vertical flip (very important on many Intel setups)
        buffer = buffer[:, :, [3,0,1,2]]   # ARGB → RGBA
        buffer = np.flipud(buffer)          # flip vertically

        w, h = fig.canvas.get_width_height()
        texture = Texture.create(size=(w, h), colorfmt='rgba', bufferfmt='ubyte')
        texture.blit_buffer(buffer.tobytes(), colorfmt='rgba', bufferfmt='ubyte')

        self.plot_widget.texture = texture

        # Force redraw (two-step helps on some compositors)
        self.plot_widget.canvas.ask_update()
        Clock.schedule_once(lambda dt: self.plot_widget.canvas.ask_update(), 0.08)

        plt.close(fig)

if __name__ == '__main__':
    PortfolioApp().run()