"""
weather_gui.py
Oasis Infobyte Python Programming Internship - Project 3 (Advanced)

The "face" of the Weather App -- a Tkinter GUI. This file contains
ZERO API-calling or data-parsing logic; it only asks weather_service.py
for already-processed data and displays it. If we swapped this file
for a web frontend tomorrow, weather_service.py wouldn't need to change
at all. That's the payoff of separating logic from display.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

import weather_service as ws


# --- Simple unit conversion helpers (display layer concern only) ---

def c_to_f(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def kmh_to_mph(kmh: float) -> float:
    return kmh * 0.621371


def wind_direction_label(degrees: float) -> str:
    """Convert a wind direction in degrees to a compass label."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App - OIBSIP Task 3")
        self.geometry("560x680")
        self.minsize(480, 600)
        self.configure(bg="#eef3f8")

        self.use_fahrenheit = tk.BooleanVar(value=False)
        self.current_city_info = None  # set after a successful lookup

        self._build_layout()
        self._refresh_favorites_menu()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self):
        # --- Search bar ---
        search_frame = tk.Frame(self, bg="#eef3f8", padx=12, pady=12)
        search_frame.pack(fill="x")

        self.city_entry = tk.Entry(search_frame, font=("Segoe UI", 13))
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.city_entry.bind("<Return>", lambda event: self.search_weather())
        self.city_entry.insert(0, "Enter a city name...")
        self.city_entry.bind("<FocusIn>", self._clear_placeholder)

        search_btn = tk.Button(search_frame, text="Search", command=self.search_weather)
        search_btn.pack(side="left")

        fav_btn = tk.Button(search_frame, text="Save to Favorites", command=self.save_current_as_favorite)
        fav_btn.pack(side="left", padx=(6, 0))

        # --- Favorites dropdown ---
        fav_frame = tk.Frame(self, bg="#eef3f8", padx=12)
        fav_frame.pack(fill="x")
        tk.Label(fav_frame, text="Favorites:", bg="#eef3f8").pack(side="left")
        self.favorites_combo = ttk.Combobox(fav_frame, state="readonly")
        self.favorites_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.favorites_combo.bind("<<ComboboxSelected>>", self._on_favorite_selected)

        # --- Unit toggle ---
        unit_frame = tk.Frame(self, bg="#eef3f8", padx=12, pady=4)
        unit_frame.pack(fill="x")
        tk.Checkbutton(
            unit_frame, text="Show \u00b0F (default \u00b0C)", variable=self.use_fahrenheit,
            bg="#eef3f8", command=self._rerender_if_loaded,
        ).pack(side="left")

        # --- Stale-data warning banner (hidden by default) ---
        self.stale_banner = tk.Label(
            self, text="[Offline] Showing last saved data \u2014 network unavailable",
            bg="#fff3cd", fg="#856404", font=("Segoe UI", 10, "bold"), pady=4,
        )
        # not packed yet; shown only when needed

        # --- Approximate-match info banner (hidden by default) ---
        self.approx_banner = tk.Label(
            self, text="", bg="#d1ecf1", fg="#0c5460",
            font=("Segoe UI", 10, "bold"), pady=4, wraplength=520, justify="left",
        )
        # not packed yet; shown only when needed

        # --- Scrollable result area ---
        container = tk.Frame(self, bg="#eef3f8")
        container.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        canvas = tk.Canvas(container, bg="#eef3f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.result_frame = tk.Frame(canvas, bg="#eef3f8")

        self.result_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.result_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_label = tk.Label(
            self.result_frame, text="Search for a city to see the weather.",
            bg="#eef3f8", font=("Segoe UI", 12), fg="#555",
        )
        self.status_label.pack(pady=40)

        self._last_render_data = None  # cached for unit-toggle re-render

    def _clear_placeholder(self, event):
        if self.city_entry.get() == "Enter a city name...":
            self.city_entry.delete(0, tk.END)

    # ------------------------------------------------------------------
    # Search flow
    # ------------------------------------------------------------------

    def search_weather(self):
        city_name = self.city_entry.get().strip()
        if not city_name or city_name == "Enter a city name...":
            messagebox.showinfo("Input needed", "Please enter a city name.")
            return

        self._set_status(f"Searching for '{city_name}'...")
        # Run network calls on a background thread so the GUI doesn't freeze
        threading.Thread(target=self._fetch_and_render, args=(city_name,), daemon=True).start()

    def _fetch_and_render(self, city_name: str):
        try:
            city_info = ws.geocode_city(city_name)
            cache_key = f"{city_info['name']}_{city_info['country']}"
            weather_data = ws.get_weather(city_info["latitude"], city_info["longitude"], cache_key)

        except ws.LocationNotFoundError as exc:
            # Capture everything we need as plain values NOW -- Python
            # deletes the 'exc' variable as soon as this except block
            # ends, so a lambda scheduled via self.after() would
            # otherwise try to reference a variable that no longer
            # exists by the time it actually runs.
            query = exc.query
            suggestions = exc.suggestions
            self.after(0, lambda: self._set_not_found(query, suggestions))
            return

        except ws.WeatherServiceError as exc:
            error_message = str(exc)
            self.after(0, lambda: self._set_status(error_message))
            return

        except Exception as exc:
            # Safety net: catch anything unexpected so the UI never hangs
            # silently on "Searching..." -- always show *some* feedback.
            error_message = f"Something went wrong while looking that up: {exc}"
            self.after(0, lambda: self._set_status(error_message))
            return

        self.current_city_info = city_info
        # Tkinter isn't thread-safe -- hand off back to the main thread
        self.after(0, lambda: self._render_weather(city_info, weather_data))

    def _rerender_if_loaded(self):
        if self._last_render_data:
            city_info, weather_data = self._last_render_data
            self._render_weather(city_info, weather_data)

    # ------------------------------------------------------------------
    # Status / error rendering
    # ------------------------------------------------------------------

    def _clear_banners_and_results(self):
        self.stale_banner.pack_forget()
        self.approx_banner.pack_forget()
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def _set_status(self, text: str):
        self._clear_banners_and_results()
        tk.Label(self.result_frame, text=text, bg="#eef3f8",
                  font=("Segoe UI", 12), fg="#555", wraplength=500, justify="left").pack(pady=40)

    def _set_not_found(self, query: str, suggestions: list):
        """
        Shown when a place couldn't be resolved at all. If we have
        "did you mean?" suggestions, offer them as clickable buttons
        so the user can recover in one click instead of retyping.
        """
        self._clear_banners_and_results()

        tk.Label(
            self.result_frame, text=f"Couldn't find '{query}'.", bg="#eef3f8",
            font=("Segoe UI", 13, "bold"), fg="#a94442",
        ).pack(anchor="w", pady=(30, 4), padx=8)

        if suggestions:
            tk.Label(
                self.result_frame, text="Did you mean:", bg="#eef3f8",
                font=("Segoe UI", 11), fg="#555",
            ).pack(anchor="w", padx=8, pady=(4, 4))

            for suggestion in suggestions:
                label = suggestion["name"]
                if suggestion.get("admin1"):
                    label += f", {suggestion['admin1']}"
                label += f", {suggestion['country']}"

                # Default-argument trick: binds THIS suggestion to THIS
                # button. Without it, every button in the loop would end
                # up referencing whatever "suggestion" happens to be by
                # the time it's clicked (the last one in the list) --
                # a classic late-binding closure bug in Python loops.
                btn = tk.Button(
                    self.result_frame, text=label, anchor="w",
                    command=lambda s=suggestion: self._search_suggestion(s),
                )
                btn.pack(fill="x", padx=8, pady=2)
        else:
            tk.Label(
                self.result_frame,
                text="Please check the spelling, or try the name of a nearby city or town instead.",
                bg="#eef3f8", font=("Segoe UI", 10), fg="#666",
                wraplength=500, justify="left",
            ).pack(anchor="w", padx=8, pady=(4, 0))

    def _search_suggestion(self, suggestion: dict):
        """Called when a 'did you mean?' button is clicked."""
        display_name = suggestion["name"]
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, display_name)
        self.search_weather()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_weather(self, city_info: dict, weather_data: dict):
        self._last_render_data = (city_info, weather_data)
        self._clear_banners_and_results()

        # Stale-data banner
        if weather_data.get("_stale"):
            self.stale_banner.pack(fill="x", before=self.result_frame.master.master)

        # Approximate-match banner: geocoding fell back to a broader place
        if not city_info.get("is_exact_match", True):
            query = city_info.get("query", "")
            resolved = city_info["name"]
            region = f", {city_info['admin1']}" if city_info.get("admin1") else ""
            self.approx_banner.config(
                text=(
                    f"We don't have data for the exact location '{query}'. "
                    f"Showing results for the nearest known place: {resolved}{region}, {city_info['country']}."
                )
            )
            self.approx_banner.pack(fill="x", before=self.result_frame.master.master)

        current = weather_data["weather"]["current"]
        hourly = weather_data["weather"]["hourly"]
        daily = weather_data["weather"]["daily"]
        aqi_current = weather_data["air_quality"]["current"]

        unit_symbol = "\u00b0F" if self.use_fahrenheit.get() else "\u00b0C"

        def fmt_temp(celsius_value):
            if celsius_value is None:
                return "N/A"
            value = c_to_f(celsius_value) if self.use_fahrenheit.get() else celsius_value
            return f"{value:.1f}{unit_symbol}"

        # --- Header: location + current conditions ---
        location_str = f"{city_info['name']}"
        if city_info.get("admin1"):
            location_str += f", {city_info['admin1']}"
        location_str += f", {city_info['country']}"

        header = tk.Label(
            self.result_frame, text=location_str, bg="#eef3f8",
            font=("Segoe UI", 18, "bold"),
        )
        header.pack(anchor="w", pady=(4, 0))

        condition_desc = ws.describe_weather_code(current["weather_code"])
        cond_label = tk.Label(
            self.result_frame, text=condition_desc, bg="#eef3f8",
            font=("Segoe UI", 12), fg="#444",
        )
        cond_label.pack(anchor="w")

        temp_big = tk.Label(
            self.result_frame, text=fmt_temp(current["temperature_2m"]),
            bg="#eef3f8", font=("Segoe UI", 40, "bold"),
        )
        temp_big.pack(anchor="w", pady=(4, 0))

        feels_explanation = ws.feels_like_explanation(
            current["temperature_2m"], current["apparent_temperature"]
        )
        feels_label = tk.Label(
            self.result_frame,
            text=f"Feels like {fmt_temp(current['apparent_temperature'])} \u2014 {feels_explanation}",
            bg="#eef3f8", font=("Segoe UI", 10), fg="#666", wraplength=500, justify="left",
        )
        feels_label.pack(anchor="w", pady=(0, 8))

        # --- Trend ---
        trend_text = ws.compute_trend(hourly["time"], hourly["temperature_2m"])
        if trend_text:
            tk.Label(
                self.result_frame, text=f"Trend: {trend_text}", bg="#eef3f8",
                font=("Segoe UI", 10, "italic"), fg="#2a6f97",
            ).pack(anchor="w", pady=(0, 10))

        # --- Info grid: wind, precipitation, sunrise/sunset ---
        grid = tk.Frame(self.result_frame, bg="#eef3f8")
        grid.pack(fill="x", pady=8)

        wind_speed = current["wind_speed_10m"]
        wind_speed_display = (
            f"{kmh_to_mph(wind_speed):.1f} mph" if self.use_fahrenheit.get()
            else f"{wind_speed:.1f} km/h"
        )
        wind_dir = wind_direction_label(current["wind_direction_10m"])
        self._add_info_tile(grid, 0, 0, "Wind", f"{wind_speed_display} {wind_dir}")

        precip_prob_today = daily["precipitation_probability_max"][1] if len(daily["precipitation_probability_max"]) > 1 else "N/A"
        self._add_info_tile(grid, 0, 1, "Rain Chance", f"{precip_prob_today}%")

        sunrise = daily["sunrise"][1].split("T")[1] if len(daily["sunrise"]) > 1 else "N/A"
        sunset = daily["sunset"][1].split("T")[1] if len(daily["sunset"]) > 1 else "N/A"
        self._add_info_tile(grid, 1, 0, "Sunrise", sunrise)
        self._add_info_tile(grid, 1, 1, "Sunset", sunset)

        # --- Air Quality ---
        aqi_value = aqi_current.get("us_aqi")
        aqi_category, aqi_advice = ws.interpret_aqi(aqi_value)
        self._add_section(
            "Air Quality",
            f"AQI {aqi_value if aqi_value is not None else 'N/A'} \u2014 {aqi_category}",
            aqi_advice,
        )

        # --- UV Index ---
        uv_today = daily["uv_index_max"][1] if len(daily["uv_index_max"]) > 1 else None
        uv_category, uv_advice = ws.interpret_uv(uv_today)
        self._add_section(
            "UV Index",
            f"{uv_today if uv_today is not None else 'N/A'} \u2014 {uv_category}",
            uv_advice,
        )

        # --- Daily min/max ---
        if len(daily["temperature_2m_max"]) > 1:
            high = fmt_temp(daily["temperature_2m_max"][1])
            low = fmt_temp(daily["temperature_2m_min"][1])
            self._add_section("Today's Range", f"High {high} / Low {low}", "")

    def _add_info_tile(self, parent, row, col, title, value):
        tile = tk.Frame(parent, bg="#ffffff", padx=10, pady=8)
        tile.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(tile, text=title, bg="#ffffff", font=("Segoe UI", 9), fg="#777").pack(anchor="w")
        tk.Label(tile, text=value, bg="#ffffff", font=("Segoe UI", 13, "bold")).pack(anchor="w")

    def _add_section(self, title, headline, subtext):
        section = tk.Frame(self.result_frame, bg="#ffffff", padx=12, pady=10)
        section.pack(fill="x", pady=4)
        tk.Label(section, text=title, bg="#ffffff", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(section, text=headline, bg="#ffffff", font=("Segoe UI", 13)).pack(anchor="w", pady=(2, 2))
        if subtext:
            tk.Label(
                section, text=subtext, bg="#ffffff", font=("Segoe UI", 9),
                fg="#666", wraplength=480, justify="left",
            ).pack(anchor="w")

    # ------------------------------------------------------------------
    # Favorites
    # ------------------------------------------------------------------

    def save_current_as_favorite(self):
        if not self.current_city_info:
            messagebox.showinfo("Nothing to save", "Search for a city first.")
            return
        ws.save_favorite(self.current_city_info)
        self._refresh_favorites_menu()
        messagebox.showinfo("Saved", f"{self.current_city_info['name']} added to favorites.")

    def _refresh_favorites_menu(self):
        favorites = ws.load_favorites()
        labels = [f"{f['name']}, {f['country']}" for f in favorites]
        self.favorites_combo["values"] = labels
        self._favorites_data = favorites

    def _on_favorite_selected(self, event):
        index = self.favorites_combo.current()
        if index < 0:
            return
        city_info = self._favorites_data[index]
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city_info["name"])
        self.search_weather()


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()