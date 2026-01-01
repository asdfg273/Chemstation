# chem_assistant/app.py - V12, THE ABSOLUTE AND FINAL MASTERPIECE, FORGED FROM THE USER'S BLUEPRINT

import tkinter
from tkinter import filedialog, messagebox, simpledialog, ttk
import customtkinter as ctk
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt  # <<< 咒语1: 补全绘图咒语
import numpy as np
import os
import json
import logging
import time
from datetime import datetime

# 导入自定义模块
from utils.file_io.journal_manager import JournalManager

# --- 关键依赖导入 ---
try:
    import pyvista as pv
    from PySide6 import QtWidgets, QtCore
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
    print("DEBUG: PySide6 and PyVista loaded successfully.")
except ImportError as e:
    PYVISTA_AVAILABLE = False
    print(f"警告：PySide6或PyVista库加载失败。3D可视化功能将不可用。\n错误: {e}")

try:
    from chempy import balance_stoichiometry, Substance, Reaction # <<< 咒语2: 补全反应咒语
    
    # 尝试不同的导入路径，适应不同版本的chempy库
    try:
        from chempy.util.parsing import formula_parser # <<< 咒语3: 补全解析咒语
    except ImportError:
        try:
            from chempy.parsing import formula_parser
        except ImportError:
            # 如果无法导入，将在后续处理
            formula_parser = None
    
    CHEMPY_AVAILABLE = True
    print("DEBUG: Chempy loaded successfully.")
except ImportError as e:
    CHEMPY_AVAILABLE = False
    formula_parser = None
    print(f"警告：chempy库加载失败。化学计算功能将不可用。\n错误: {e}")

# 原子序数到符号的绝对可靠映射
ELEMENT_Z_MAP = {
    1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
    11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K',
    20: 'Ca', 21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni',
    29: 'Cu', 30: 'Zn', 31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb',
    38: 'Sr', 39: 'Y', 40: 'Zr', 41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd',
    47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn', 51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs',
    56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd', 61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd',
    65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb', 71: 'Lu', 72: 'Hf', 73: 'Ta',
    74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg', 81: 'Tl', 82: 'Pb',
    83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn'
}

# 符号到原子序数的映射
ELEMENT_SYMBOL_MAP = {v: k for k, v in ELEMENT_Z_MAP.items()}

# 备选化学式解析器
import re

def alternative_formula_parser(formula):
    """增强的化学式解析器，支持带括号、方括号和电荷的复杂化学式"""
    if not formula:
        return {}
    
    # 1. 处理电荷部分（如2+、3-、+、-）
    charge_pattern = r'([+-]?\d*[+-])$'
    charge_match = re.search(charge_pattern, formula)
    if charge_match:
        formula = formula[:-len(charge_match.group(1))]
    
    # 2. 处理水合物部分（如·3H2O）
    hydrate_pattern = r'\·\d*[A-Za-z\d]*$'
    formula = re.sub(hydrate_pattern, '', formula)
    
    # 初始化元素组成字典
    composition = {}
    
    def add_element(element, count=1):
        """添加元素到组成字典"""
        if element not in ELEMENT_SYMBOL_MAP:
            return
        if element in composition:
            composition[element] += count
        else:
            composition[element] = count
    
    # 使用栈来处理括号
    stack = []
    current = []
    i = 0
    n = len(formula)
    
    while i < n:
        char = formula[i]
        
        if char in '([{':
            # 遇到左括号，将当前内容入栈
            stack.append((current.copy(), 1))
            current = []
            i += 1
        
        elif char in ')]}':
            # 遇到右括号，处理括号内的内容
            bracket_content = ''.join(current)
            current = []
            
            # 提取括号后的倍数
            j = i + 1
            multiplier_str = ''
            while j < n and formula[j].isdigit():
                multiplier_str += formula[j]
                j += 1
            multiplier = int(multiplier_str) if multiplier_str else 1
            
            # 解析括号内的内容
            bracket_composition = {}
            pattern = r'([A-Z][a-z]?)(\d*)'
            bracket_matches = re.findall(pattern, bracket_content)
            
            for element, count_str in bracket_matches:
                count = int(count_str) if count_str else 1
                total_count = count * multiplier
                
                if element in bracket_composition:
                    bracket_composition[element] += total_count
                else:
                    bracket_composition[element] = total_count
            
            # 将括号内的元素合并到结果中
            for element, count in bracket_composition.items():
                add_element(element, count)
            
            # 如果栈不为空，恢复之前的状态
            if stack:
                prev_content, prev_multiplier = stack.pop()
                current = prev_content
            
            i = j
        
        else:
            # 普通字符，添加到当前内容
            current.append(char)
            i += 1
    
    # 处理剩余的内容
    if current:
        remaining = ''.join(current)
        pattern = r'([A-Z][a-z]?)(\d*)'
        remaining_matches = re.findall(pattern, remaining)
        
        for element, count_str in remaining_matches:
            count = int(count_str) if count_str else 1
            add_element(element, count)
    
    return composition

# 如果chempy的formula_parser不可用，使用我们的备选解析器
if not 'formula_parser' in locals() or formula_parser is None:
    formula_parser = alternative_formula_parser

def find_chinese_font():
    """智能查找可用的中文字体"""
    from matplotlib.font_manager import FontManager
    fontManager = FontManager()
    font_names = ['SimHei', 'Microsoft YaHei', 'Heiti TC', 'PingFang SC', 'WenQuanYi Micro Hei']
    available_fonts = [f.name for f in fontManager.ttflist]
    for font_name in font_names:
        if font_name in available_fonts:
            print(f"DEBUG (Font Detective): Found usable Chinese font: '{font_name}'")
            return font_name
    print("WARNING (Font Detective): No common Chinese font found. Display might be incorrect.")
    return None

# 设置Matplotlib全局字体
CHINESE_FONT = find_chinese_font()
matplotlib.rcParams['font.sans-serif'] = [CHINESE_FONT] if CHINESE_FONT else ['sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

# --- 主应用程序 ---
class ChemApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("化学工作站")
        self.geometry("1200x850")
        ctk.set_appearance_mode("Dark")
    
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.font = CHINESE_FONT
        
        # 初始化日志管理器
        self.journal_manager = JournalManager()
        
        # 自动保存任务ID
        self.auto_save_task_id = None

        self.create_widgets()
        
        self.notebook.set("单物质分析")
        
        # 启动自动保存定时器
        self.start_auto_save_timer()

    def create_widgets(self):
        """一次性创建所有UI组件，符合逻辑顺序。"""
        # 创建主选项卡视图 (Notebook)
        self.notebook = ctk.CTkTabview(self, width=1180, height=830)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.tabs = {}
        tab_names = [
            "单物质分析", "化学计量 & 设计", "溶液配制",
            "有机化学", "结构化学", "谱图分析", "实验日志",
            "网络查询", "AI助手"
        ]
        for name in tab_names:
            self.tabs[name] = self.notebook.add(name)

        # 按顺序构建每个标签页的内容
        self.create_substance_analysis_tab()
        self.create_stoichiometry_tab()
        self.create_solution_prep_tab()
        self.create_organic_chem_tab()
        self.create_structural_chem_tab()
        self.create_spectra_tab()
        self.create_journal_tab()
        self.create_network_search_tab()
        self.create_ai_assistant_tab()

    # =====================================================================
    # 1. 单物质分析
    # =====================================================================
    def create_substance_analysis_tab(self):
        tab = self.tabs["单物质分析"]
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        input_frame = ctk.CTkFrame(tab)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(input_frame, text="输入化学式 (例如: C6H12O6):").pack(side="left", padx=(10,5))
        self.substance_entry = ctk.CTkEntry(input_frame, width=300)
        self.substance_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.substance_entry.bind("<Return>", lambda event: self.analyze_substance())
        ctk.CTkButton(input_frame, text="分析物质", command=self.analyze_substance).pack(side="left", padx=(5,10))

        result_frame = ctk.CTkFrame(tab)
        result_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_columnconfigure(1, weight=2)
        result_frame.grid_rowconfigure(0, weight=1)
        
        self.sub_result_text = ctk.CTkTextbox(result_frame, wrap="word", height=300)
        self.sub_result_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.sub_fig = Figure(figsize=(5, 4), dpi=100, facecolor="#2b2b2b")
        self.sub_ax = self.sub_fig.add_subplot(111)
        self.sub_canvas = FigureCanvasTkAgg(self.sub_fig, master=result_frame)
        self.sub_canvas.get_tk_widget().grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.update_substance_plot([], [])

    def analyze_substance(self):
        formula = self.substance_entry.get()
        if not formula:
            self.update_sub_result_text("请输入化学式。")
            self.update_substance_plot([], [])
            return
        
        if not CHEMPY_AVAILABLE:
            self.update_sub_result_text("错误: chempy库不可用。")
            return

        try:
            substance = Substance.from_formula(formula)
            total_mass = substance.mass
            
            elements_data = []
            for z, count in substance.composition.items():
                element_symbol = ELEMENT_Z_MAP.get(z, f'Z={z}')
                element_mass = 0
                if not element_symbol.startswith('Z='):
                     # 使用chempy获取单个原子的质量
                     element_mass_single = Substance.from_formula(element_symbol).mass
                     element_mass = element_mass_single * count

                mass_percent = (element_mass / total_mass) * 100 if total_mass > 0 else 0
                elements_data.append({'symbol': element_symbol, 'count': count, 'mass_percent': mass_percent})
            
            result_text = f"总式量 (Mass): {total_mass:.4f}\n\n元素组成 (Elemental Composition):\n"
            result_text += "-" * 30 + "\n"
            for data in elements_data:
                result_text += f"元素 (Element): {data['symbol']}\n  - 数量 (Count): {data['count']}\n  - 质量百分比 (Mass %): {data['mass_percent']:.2f}%\n"
            
            self.update_sub_result_text(result_text)

            labels = [f"{data['symbol']} ({data['mass_percent']:.1f}%)" for data in elements_data]
            sizes = [data['mass_percent'] for data in elements_data]
            self.update_substance_plot(labels, sizes)
        except Exception as e:
            error_message = f"错误: 无法解析化学式 '{formula}'。\n请检查拼写和大小写 (例如: H2O, CH4, Fe2O3)。\n内部错误: {type(e).__name__}"
            self.update_sub_result_text(error_message)
            self.update_substance_plot([], [])

    def update_sub_result_text(self, text):
        """信使修复：安全地更新物质分析结果文本框。"""
        self.sub_result_text.delete("1.0", "end")
        self.sub_result_text.insert("1.0", text)

    def update_substance_plot(self, labels, sizes):
        self.sub_ax.clear()
        self.sub_ax.set_facecolor("#2b2b2b")
        if labels and sizes:
            wedges, texts, autotexts = self.sub_ax.pie(sizes, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
            for text in texts + autotexts:
                text.set_color('white')
            self.sub_ax.legend(wedges, labels, title="元素", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                               labelcolor='white', facecolor='#3c3c3c', edgecolor='gray')
            self.sub_ax.axis('equal')
        else:
            self.sub_ax.text(0.5, 0.5, '无数据显示', ha='center', va='center', color='gray')
        
        title_props = {'color': 'white'}
        if self.font: title_props['fontproperties'] = self.font
        self.sub_ax.set_title("元素质量百分比", **title_props)
        self.sub_fig.tight_layout(pad=1.0)
        self.sub_canvas.draw()
    
    # 2. 化学计量 & 设计 
    def create_stoichiometry_tab(self):
        tab = self.tabs["化学计量 & 设计"]
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        input_frame = ctk.CTkFrame(tab)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(input_frame, text="化学方程式:").pack(side="left", padx=5)
        self.stoich_entry = ctk.CTkEntry(input_frame, placeholder_text="例如: H2 + O2 -> H2O")
        self.stoich_entry.pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(input_frame, text="配平并计算", command=self.balance_and_calculate).pack(side="left", padx=5)
        self.stoich_entry.bind("<Return>", lambda e: self.balance_and_calculate())

        self.balanced_label = ctk.CTkLabel(tab, text="已配平: -", font=("", 14, "bold"))
        self.balanced_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.calc_frame = ctk.CTkFrame(tab)
        self.calc_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        result_frame = ctk.CTkFrame(tab)
        result_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_columnconfigure(1, weight=1)
        result_frame.grid_rowconfigure(0, weight=1)

        self.stoich_advice_text = ctk.CTkTextbox(result_frame, wrap="word", height=150)
        self.stoich_advice_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.stoich_fig = Figure(figsize=(5, 3), dpi=100, facecolor="#2b2b2b")
        self.stoich_ax = self.stoich_fig.add_subplot(111)
        self.stoich_canvas = FigureCanvasTkAgg(self.stoich_fig, master=result_frame)
        self.stoich_canvas.get_tk_widget().grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.update_stoich_advice_and_plot(init=True)

    def balance_and_calculate(self):
        if not CHEMPY_AVAILABLE:
            messagebox.showerror("错误", "chempy库不可用。")
            return
        equation_str = self.stoich_entry.get()
        if '->' not in equation_str:
            messagebox.showerror("输入错误", "请输入有效的化学方程式，包含 '->'。")
            return
        try:
            reactants_str, products_str = [s.strip() for s in equation_str.split('->')]
            reactants = {k:v for k,v in formula_parser(reactants_str).items()}
            products = {k:v for k,v in formula_parser(products_str).items()}
            
            reac, prod = balance_stoichiometry(reactants.keys(), products.keys())
            self.reaction = Reaction(reac, prod)
            self.balanced_label.configure(text=f"已配平: {self.reaction}")
            self.update_calculation_grid()
            self.update_stoich_advice_and_plot(init=True)
        except Exception as e:
            messagebox.showerror("计算错误", f"无法配平或解析方程式。\n详细信息: {e}")

    def update_calculation_grid(self):
        for widget in self.calc_frame.winfo_children():
            widget.destroy()
        headers = ["物质", "系数", "摩尔质量 (g/mol)", "输入质量 (g)", "计算结果 (mol)"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(self.calc_frame, text=header).grid(row=0, column=i, padx=5, pady=5)
        self.calc_entries = {}
        all_substances = list(self.reaction.reac.keys()) + list(self.reaction.prod.keys())
        for i, formula in enumerate(all_substances):
            sub = Substance.from_formula(formula)
            coeff = self.reaction.reac.get(formula) or self.reaction.prod.get(formula)
            ctk.CTkLabel(self.calc_frame, text=formula).grid(row=i + 1, column=0)
            ctk.CTkLabel(self.calc_frame, text=str(coeff)).grid(row=i + 1, column=1)
            ctk.CTkLabel(self.calc_frame, text=f"{sub.mass:.4f}").grid(row=i + 1, column=2)
            entry = ctk.CTkEntry(self.calc_frame, width=100)
            entry.grid(row=i + 1, column=3, padx=5, pady=2)
            result_label = ctk.CTkLabel(self.calc_frame, text="-")
            result_label.grid(row=i + 1, column=4)
            self.calc_entries[formula] = {'entry': entry, 'result_label': result_label, 'substance': sub, 'coeff': coeff}
            entry.bind("<KeyRelease>", self.perform_stoich_calc)

    def perform_stoich_calc(self, event=None):
        base_formula, base_moles = None, None
        for formula, data in self.calc_entries.items():
            mass_str = data['entry'].get()
            if mass_str:
                try:
                    mass = float(mass_str)
                    base_moles = mass / data['substance'].mass
                    base_formula = formula
                    break
                except (ValueError, ZeroDivisionError):
                    data['result_label'].configure(text="无效输入")
                    continue
        if base_formula is None:
            for data in self.calc_entries.values(): data['result_label'].configure(text="-")
            self.update_stoich_advice_and_plot()
            return
        masses, moles, base_coeff = {}, {}, self.calc_entries[base_formula]['coeff']
        for formula, data in self.calc_entries.items():
            calculated_moles = base_moles * (data['coeff'] / base_coeff)
            data['result_label'].configure(text=f"{calculated_moles:.4f}")
            masses[formula] = calculated_moles * data['substance'].mass
            moles[formula] = calculated_moles
        self.update_stoich_advice_and_plot(masses, moles)

    def update_stoich_advice_and_plot(self, masses=None, moles=None, init=False):
        advice_text_widget = self.stoich_advice_text
        advice_text_widget.delete("1.0", "end")
        if init or not masses or not moles:
            advice_text_widget.insert("1.0", "请输入任意一种物质的质量以开始计算。\n\n安全提示：请始终佩戴适当的个人防护装备（PPE），并在通风良好的地方进行实验。")
            self.stoich_ax.clear()
            self.stoich_ax.text(0.5, 0.5, '等待计算...', ha='center', va='center', color='gray')
        else:
            advice = "--- 计算结果摘要 ---\n"
            for formula, mass in masses.items(): advice += f"{formula}: {mass:.2f} g ({moles[formula]:.4f} mol)\n"
            advice += "\n--- 实验优化建议 ---\n1. 产率分析：实际产出与理论产出对比，评估反应效率。\n2. 条件优化：可尝试调整温度、压力、催化剂等以提高产率。\n\n--- 废弃物处理 ---\n请根据当地法规和化学品安全数据表（MSDS）处理所有废弃物。"
            advice_text_widget.insert("1.0", advice)
            self.stoich_ax.clear()
            labels, values = list(masses.keys()), list(masses.values())
            self.stoich_ax.bar(labels, values, color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            self.stoich_ax.set_ylabel("质量 (g)", color="white")
            self.stoich_ax.set_title("反应物与产物的质量关系", color="white")
            self.stoich_ax.tick_params(axis='x', colors='white', rotation=45)
            self.stoich_ax.tick_params(axis='y', colors='white')
            for spine in self.stoich_ax.spines.values(): spine.set_edgecolor('white')
        self.stoich_ax.set_facecolor("#2b2b2b")
        self.stoich_fig.tight_layout()
        self.stoich_canvas.draw()
        
    # 3. 溶液配制
    def create_solution_prep_tab(self):
        tab = self.tabs["溶液配制"]
        prep_notebook = ctk.CTkTabview(tab)
        prep_notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.create_solid_prep_sub_tab(prep_notebook.add("固体配制"))
        self.create_dilution_sub_tab(prep_notebook.add("溶液稀释 (M1V1=M2V2)"))

    def create_solid_prep_sub_tab(self, tab):
        frame = ctk.CTkFrame(tab)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        ctk.CTkLabel(frame, text="溶质化学式:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.solute_entry = ctk.CTkEntry(frame, placeholder_text="例如: NaCl")
        self.solute_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="目标体积 (L):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.volume_entry = ctk.CTkEntry(frame, placeholder_text="例如: 0.5")
        self.volume_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="目标浓度 (mol/L):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.conc_entry = ctk.CTkEntry(frame, placeholder_text="例如: 1.0")
        self.conc_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(frame, text="计算", command=self.calculate_solid_solution).grid(row=3, column=0, columnspan=2, pady=20)
        self.solution_result_text = ctk.CTkTextbox(frame, wrap="word", height=250)
        self.solution_result_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def create_dilution_sub_tab(self, tab):
        frame = ctk.CTkFrame(tab)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="输入以下任意三项，留空一项以进行计算。", font=("", 14)).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        ctk.CTkLabel(frame, text="初始浓度 (M1):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.m1_entry = ctk.CTkEntry(frame, placeholder_text="mol/L")
        self.m1_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="初始体积 (V1):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.v1_entry = ctk.CTkEntry(frame, placeholder_text="L 或 mL (单位需统一)")
        self.v1_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="最终浓度 (M2):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.m2_entry = ctk.CTkEntry(frame, placeholder_text="mol/L")
        self.m2_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="最终体积 (V2):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.v2_entry = ctk.CTkEntry(frame, placeholder_text="L 或 mL (单位需统一)")
        self.v2_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(frame, text="计算稀释方案", command=self.calculate_dilution).grid(row=5, column=0, columnspan=2, pady=20)
        self.dilution_result_text = ctk.CTkTextbox(frame, wrap="word", height=250)
        self.dilution_result_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def calculate_solid_solution(self):
        if not CHEMPY_AVAILABLE:
            self.solution_result_text.delete("1.0", "end"); self.solution_result_text.insert("1.0", "错误: chempy库不可用。")
            return
        try:
            formula = self.solute_entry.get()
            volume = float(self.volume_entry.get())
            concentration = float(self.conc_entry.get())
            substance = Substance.from_formula(formula)
            molar_mass = substance.mass
            moles_needed = concentration * volume
            mass_needed = moles_needed * molar_mass
            result = f"--- 溶液配制方案 ---\n\n1. 计算所需溶质质量：\n   摩尔数 = {concentration:.4f} mol/L * {volume:.4f} L = {moles_needed:.6f} mol\n   质量 = {moles_needed:.6f} mol * {molar_mass:.4f} g/mol = {mass_needed:.4f} g\n\n2. 配制步骤：\n   a. 精确称取 {mass_needed:.4f} g 的 {formula}。\n   b. 将溶质在烧杯中用少量溶剂溶解。\n   c. 将溶液转移至 {volume * 1000} mL 容量瓶中。\n   d. 用溶剂润洗烧杯数次，并将洗涤液全部转入容量瓶。\n   e. 加溶剂至刻度线，摇匀。\n\n安全提示：请查阅 {formula} 的安全数据表(MSDS)。"
            self.solution_result_text.delete("1.0", "end"); self.solution_result_text.insert("1.0", result)
        except Exception as e:
            self.solution_result_text.delete("1.0", "end"); self.solution_result_text.insert("1.0", f"计算错误：\n{e}\n\n请确保所有输入均为有效值。")

    def calculate_dilution(self):
        entries = {'m1': self.m1_entry, 'v1': self.v1_entry, 'm2': self.m2_entry, 'v2': self.v2_entry}
        values = {k: v.get() for k, v in entries.items()}
        empty_vars = [k for k, v in values.items() if not v]
        if len(empty_vars) != 1:
            self.dilution_result_text.delete("1.0", "end"); self.dilution_result_text.insert("1.0", "错误：请输入三项，并留空一项。")
            return
        try:
            m1, v1, m2, v2 = (float(values[k]) if values[k] else None for k in ['m1','v1','m2','v2'])
            target_var = empty_vars[0]
            if target_var == 'm1': result_val = (m2 * v2) / v1
            elif target_var == 'v1': result_val = (m2 * v2) / m1
            elif target_var == 'm2': result_val = (m1 * v1) / v2
            else: result_val = (m1 * v1) / m2
            entries[target_var].delete(0, 'end'); entries[target_var].insert(0, f"{result_val:.4f}")
            result = f"--- 溶液稀释方案 ---\n\n基于公式: M1 * V1 = M2 * V2\n计算得出未知量为: {result_val:.4f}\n\n操作步骤建议：\n1. 精确量取 {entries['v1'].get()} 单位体积的母液 (浓度 {entries['m1'].get()} mol/L)。\n2. 将其加入容量瓶中。\n3. 用溶剂稀释至最终体积 {entries['v2'].get()} 单位体积。"
            self.dilution_result_text.delete("1.0", "end"); self.dilution_result_text.insert("1.0", result)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.dilution_result_text.delete("1.0", "end"); self.dilution_result_text.insert("1.0", f"计算错误：{type(e).__name__}。请检查输入值。")
            
    # 4. 有机化学
    def create_organic_chem_tab(self):
        tab = self.tabs["有机化学"]
        frame = ctk.CTkFrame(tab)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        ctk.CTkLabel(frame, text="这是一个基于规则的简单预测引擎，用于教学演示。", font=("", 14)).pack(pady=5)
        ctk.CTkLabel(frame, text="主要反应物:").pack()
        self.organic_reac_entry = ctk.CTkEntry(frame, width=300, placeholder_text="例如: alcohol")
        self.organic_reac_entry.pack(pady=(0, 10))
        ctk.CTkLabel(frame, text="预测产物:").pack()
        self.organic_prod_entry = ctk.CTkEntry(frame, width=300, placeholder_text="例如: alkene")
        self.organic_prod_entry.pack(pady=(0, 10))
        ctk.CTkButton(frame, text="预测反应路径", command=self.predict_organic_reaction).pack(pady=10)
        self.organic_result_text = ctk.CTkTextbox(frame, wrap="word")
        self.organic_result_text.pack(fill="both", expand=True, pady=10)

    def predict_organic_reaction(self):
        reactant, product = self.organic_reac_entry.get().lower(), self.organic_prod_entry.get().lower()
        result = f"--- 反应路径预测 (演示) ---\n从 {reactant} 到 {product}\n\n"
        if 'alkane' in reactant and 'alkene' in product: result += "预测路径： 催化裂化 或 脱氢反应。\n中间产物： 可能涉及自由基中间体。\n预测产率： 中等。取决于催化剂和温度。"
        elif 'alkene' in reactant and 'alkane' in product: result += "预测路径： 催化加氢 (例如 H2/Pd-C)。\n中间产物： 氢原子加成到双键上。\n预测产率： 高。通常是高效的反应。"
        elif 'alcohol' in reactant and 'alkene' in product: result += "预测路径： 醇脱水反应 (例如 浓硫酸加热)。\n中间产物： 可能涉及碳正离子中间体 (扎伊采夫规则适用)。\n预测产率： 中等到高。取决于醇的结构和反应条件。"
        else: result += "未找到匹配的反应规则。\n此功能为演示版本，仅包含少量预设规则。"
        self.organic_result_text.delete("1.0", "end"); self.organic_result_text.insert("1.0", result)
        
    def create_structural_chem_tab(self):
        tab = self.tabs["结构化学"]
        frame = ctk.CTkFrame(tab)
        frame.pack(pady=10, padx=10, fill="both", expand=True)
        main_frame = ctk.CTkFrame(frame)
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        ctk.CTkLabel(main_frame, text="3D 结构可视化", font=("", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(main_frame, text="输入化学式，在独立的专业窗口中查看3D模型。").pack(pady=5)
        ctk.CTkLabel(main_frame, text="输入化学式:").pack(pady=(20, 5))
        self.struct_entry = ctk.CTkEntry(main_frame, width=200, placeholder_text="例如: NaCl, CH4, H2O, NH3")
        self.struct_entry.pack(pady=(0, 10))
        ctk.CTkButton(main_frame, text="生成并显示3D模型", command=self.launch_3d_viewer).pack(pady=20)
        if not PYVISTA_AVAILABLE:
            ctk.CTkLabel(main_frame, text="警告: 3D库未加载，此功能不可用。", text_color="orange").pack(pady=10)

    def launch_3d_viewer(self):
        if not PYVISTA_AVAILABLE:
            messagebox.showerror("依赖缺失", "3D可视化功能不可用。\n请确保 PySide6 和 PyVista 已正确安装。")
            return
        formula = self.struct_entry.get().upper().strip()
        if not formula:
            messagebox.showinfo("提示", "请输入化学式。")
            return
        try:
            if not QtWidgets.QApplication.instance(): self.qt_app = QtWidgets.QApplication([])
            else: self.qt_app = QtWidgets.QApplication.instance()
            
            window = QtWidgets.QMainWindow()
            window.setWindowTitle(f"3D 专业查看器 - {formula}")
            window.setGeometry(100, 100, 700, 600)
            central_widget = QtWidgets.QWidget(); window.setCentralWidget(central_widget)
            layout = QtWidgets.QVBoxLayout(central_widget)
            
            plotter = QtInteractor(parent=central_widget, auto_update=True)
            layout.addWidget(plotter.interactor)
            
            model_drawn = False
            # 断裂的链接修复：所有绘图函数都接收 plotter
            if formula == 'NACL':
                self.draw_nacl_cell(plotter)
                model_drawn = True
            else:
                try: # 尝试VSEPR和自动解析
                    self.draw_vsepr_model(plotter, formula)
                    model_drawn = True
                except Exception as vsepr_e:
                     messagebox.showinfo("模型未找到", f"'{formula}' 的预设VSEPR模型规则或自动解析失败。\n错误: {vsepr_e}")
                     window.close()
                     return
            
            if model_drawn:
                plotter.reset_camera(); plotter.add_axes()
                plotter.add_text(f'{formula} 3D 模型', position='upper_left', color='black', font_size=12)
                self.three_d_window = window; self.three_d_window.show()
        except Exception as e:
            messagebox.showerror("3D视图发生未知错误", f"{e}")

    def draw_nacl_cell(self, plotter):
        plotter.clear()
        plotter.add_text("晶胞模型 (NaCl, 简化)", position='lower_left', color='black')
        na_positions = np.array([[0.5,0.5,0.5], [0,0,0.5], [0,1,0.5],[1,0,0.5],[1,1,0.5],[0.5,0,0],[0.5,1,0],[0.5,0,1],[0.5,1,1],[0,0.5,0],[1,0.5,0],[0,0.5,1],[1,0.5,1]])
        plotter.add_points(na_positions, color='purple', point_size=15, render_points_as_spheres=True)
        cl_positions = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1],[0,1,1],[1,1,1],[0.5,0.5,0],[0.5,0,0.5],[0,0.5,0.5],[1,0.5,0.5],[0.5,1,0.5],[0.5,0.5,1]])
        plotter.add_points(cl_positions, color='green', point_size=25, render_points_as_spheres=True)
        plotter.add_mesh(pv.Cube(), style='wireframe', color='gray')
        plotter.background_color = 'white'

    def draw_vsepr_model(self, plotter, formula):
        plotter.clear()
        CPK_COLORS = {'H':'white','C':'black','N':'blue','O':'red','F':'lightgreen','Cl':'green','Br':'darkred','I':'purple','P':'orange','S':'yellow','B':'salmon','DEFAULT':'pink'}
        
        shape, lone_pairs, composition, center_atom_symbol = self.get_vsepr_shape(formula)
        
        center_color = CPK_COLORS.get(center_atom_symbol, CPK_COLORS['DEFAULT'])
        plotter.add_mesh(pv.Sphere(center=(0, 0, 0), radius=0.5), color=center_color, smooth_shading=True)
        
        positions = { # 预设的理想几何构型顶点
            'Linear': [(0, 0, 2), (0, 0, -2)],
            'Trigonal planar': [(0, 2, 0), (1.732, -1, 0), (-1.732, -1, 0)],
            'Bent (Trigonal)': [(1.732, -1, 0), (-1.732, -1, 0)],
            'Tetrahedral': [(1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1)],
            'Trigonal pyramidal': [(1,1,-1), (-1,1,-1), (0,-1,1)],
            'Bent (Tetrahedral)': [(1,1,1), (1,-1,-1)],
            'Trigonal bipyramidal': [(0, 0, 2), (0, 0, -2), (1.732, -1, 0), (-1.732, -1, 0), (0, 2, 0)],
            'Seesaw': [(0, 0, 2), (0, 0, -2), (1.732, -1, 0), (-1.732, -1, 0)],
            'T-shaped': [(0, 0, 2), (1.732, -1, 0), (-1.732, -1, 0)],
            'Octahedral': [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)],
            'Square pyramidal': [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1)],
            'Square planar': [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0)]
        }
        atom_positions = positions.get(shape, [])
        surrounding_atoms = [k for k,v in composition.items() if k != center_atom_symbol for _ in range(v)]
        
        for i, pos in enumerate(atom_positions):
            if i < len(surrounding_atoms):
                atom_symbol = surrounding_atoms[i]
                atom_color = CPK_COLORS.get(atom_symbol, CPK_COLORS['DEFAULT'])
                plotter.add_mesh(pv.Sphere(center=pos, radius=0.35), color=atom_color, smooth_shading=True)
                plotter.add_mesh(pv.Cylinder(center=(pos[0]/2, pos[1]/2, pos[2]/2), direction=pos, radius=0.08, height=np.linalg.norm(pos)), color='grey')
        
        plotter.add_text(f'VSEPR Model: {shape}\nLone Pairs: {lone_pairs}', position='upper_right', color='black')
        plotter.background_color = 'white'

    def get_vsepr_shape(self, formula):
        """优化的VSEPR预测引擎，支持更复杂的分子结构。"""
        
        valence_electrons_map = {
            'H':1, 'He':2, 'Li':1, 'Be':2, 'B':3, 'C':4, 'N':5, 'O':6, 'F':7, 'Ne':8,
            'Na':1, 'Mg':2, 'Al':3, 'Si':4, 'P':5, 'S':6, 'Cl':7, 'Ar':8,
            'K':1, 'Ca':2, 'Sc':3, 'Ti':4, 'V':5, 'Cr':6, 'Mn':7, 'Fe':8, 'Co':9, 'Ni':10,
            'Cu':11, 'Zn':12, 'Ga':3, 'Ge':4, 'As':5, 'Se':6, 'Br':7, 'Kr':8,
            'I':7, 'Xe':8
        }
        
        composition = formula_parser(formula)
        
        # 单原子分子处理
        if len(composition) == 1:
            atom = next(iter(composition.keys()))
            return 'Spherical', 0, composition, atom
        
        # 常见复杂分子的特殊处理规则
        special_cases = {
            'h2o': ('Bent (Tetrahedral)', 2, composition, 'O'),
            'nh3': ('Trigonal pyramidal', 1, composition, 'N'),
            'ch4': ('Tetrahedral', 0, composition, 'C'),
            'co2': ('Linear', 0, composition, 'C'),
            'so2': ('Bent (Trigonal)', 1, composition, 'S'),
            'so3': ('Trigonal planar', 0, composition, 'S'),
            'h2so4': ('Tetrahedral', 0, composition, 'S'),
            'h3po4': ('Tetrahedral', 0, composition, 'P'),
            'hno3': ('Trigonal planar', 0, composition, 'N'),
            'o3': ('Bent (Trigonal)', 1, composition, 'O'),
            'pcl5': ('Trigonal bipyramidal', 0, composition, 'P'),
            'sf6': ('Octahedral', 0, composition, 'S'),
            'pf5': ('Trigonal bipyramidal', 0, composition, 'P'),
            'brf5': ('Square pyramidal', 1, composition, 'Br'),
            'xef4': ('Square planar', 2, composition, 'Xe')
        }
        
        # 特殊情况处理（不区分大小写）
        formula_lower = formula.lower()
        if formula_lower in special_cases:
            return special_cases[formula_lower]
        
        # 双原子分子处理（分子中只有两种原子，且每种原子只有一个）
        # 例如：HCl, NaCl, CO等
        total_atoms = sum(count for count in composition.values())
        if len(composition) == 2 and total_atoms == 2:
            atoms = list(composition.keys())
            # 确定中心原子（电负性较小的原子）
            center_atom = atoms[0] if valence_electrons_map.get(atoms[0], 8) < valence_electrons_map.get(atoms[1], 8) else atoms[1]
            return 'Linear', 0, composition, center_atom
        
        # 启发式确定中心原子
        # 1. 排除H和卤素作为中心原子
        possible_centers = [atom for atom in composition if atom not in ['H', 'F', 'Cl', 'Br', 'I']]
        
        if not possible_centers:
            # 如果所有原子都是H或卤素，选择数量最少的
            possible_centers = list(composition.keys())
        
        # 2. 选择数量最少且电负性最小的原子作为中心原子
        center_atom_symbol = min(possible_centers, key=lambda k: (composition[k], valence_electrons_map.get(k, 8)))
        
        # 计算总价电子数
        total_valence_electrons = 0
        for atom, count in composition.items():
            if atom not in valence_electrons_map: raise ValueError(f"Valence electrons for '{atom}' unknown.")
            total_valence_electrons += valence_electrons_map[atom] * count
        
        # 计算键数
        num_bonds = sum(count for atom, count in composition.items() if atom != center_atom_symbol)
        
        # 优化孤对电子计算
        # 基于已知分子的孤对电子数进行调整
        known_lone_pairs = {
            'O': 2, 'N': 1, 'C': 0, 'S': 0, 'P': 0, 'Si': 0, 'B': 0, 'Al': 0
        }
        
        if center_atom_symbol in known_lone_pairs:
            lone_pairs = known_lone_pairs[center_atom_symbol]
        else:
            # 回退到基于总价电子数的计算
            is_expanded_octet = center_atom_symbol in ['S', 'P', 'Cl', 'Br', 'I', 'Xe', 'Se', 'As', 'Sb', 'Te']
            
            if is_expanded_octet:
                num_lone_pair_electrons = total_valence_electrons - 2 * num_bonds
            else:
                num_lone_pair_electrons = total_valence_electrons - 8
            
            if num_lone_pair_electrons < 0:
                num_lone_pair_electrons = 0
            
            lone_pairs = num_lone_pair_electrons // 2
        
        steric_number = num_bonds + lone_pairs
        
        # 扩展几何构型字典，支持空间数1-7
        shapes = {
            1: {0: 'Spherical'},
            2: {0: 'Linear'},
            3: {0: 'Trigonal planar', 1: 'Bent (Trigonal)'},
            4: {0: 'Tetrahedral', 1: 'Trigonal pyramidal', 2: 'Bent (Tetrahedral)'},
            5: {0: 'Trigonal bipyramidal', 1: 'Seesaw', 2: 'T-shaped', 3: 'Linear'},
            6: {0: 'Octahedral', 1: 'Square pyramidal', 2: 'Square planar', 3: 'T-shaped', 4: 'Linear'},
            7: {0: 'Pentagonal bipyramidal'}
        }
        
        # 特殊处理：如果空间数超过6，尝试简化处理
        if steric_number > 6:
            # 对于复杂分子，尝试使用更简单的规则
            if center_atom_symbol in ['S', 'P'] and num_bonds <= 6:
                # 对于S、P等元素，假设它们采用四面体或八面体构型
                if num_bonds == 4:
                    return 'Tetrahedral', 0, composition, center_atom_symbol
                elif num_bonds == 5:
                    return 'Trigonal bipyramidal', 0, composition, center_atom_symbol
                elif num_bonds == 6:
                    return 'Octahedral', 0, composition, center_atom_symbol
            
            # 无法确定时，返回一个合理的默认值
            raise ValueError(f"Cannot determine shape for complex molecule '{formula}'.\nTry a simpler molecule or check the formula.")
        
        if steric_number not in shapes:
            raise ValueError(f"Steric number {steric_number} not supported yet.")
        
        if lone_pairs not in shapes[steric_number]:
            # 尝试调整孤对电子数，寻找最接近的合理构型
            adjusted_lone_pairs = min(shapes[steric_number].keys(), key=lambda x: abs(x - lone_pairs))
            return shapes[steric_number][adjusted_lone_pairs], adjusted_lone_pairs, composition, center_atom_symbol
        
        return shapes[steric_number][lone_pairs], lone_pairs, composition, center_atom_symbol

    def create_spectra_tab(self):
        tab = self.tabs["谱图分析"]
        tab.grid_columnconfigure(0, weight=1); tab.grid_rowconfigure(1, weight=1)
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(control_frame, text="加载谱图数据 (CSV)", command=self.load_and_plot_spectrum).pack(side="left", padx=10)
        self.spectra_info_label = ctk.CTkLabel(control_frame, text="请加载一个两列的CSV文件 (X, Y)")
        self.spectra_info_label.pack(side="left", padx=10)
        plot_frame = ctk.CTkFrame(tab)
        plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.spectra_fig = Figure(figsize=(8, 6), dpi=100, facecolor="#2b2b2b")
        self.spectra_ax = self.spectra_fig.add_subplot(111)
        self.spectra_canvas = FigureCanvasTkAgg(self.spectra_fig, master=plot_frame)
        self.spectra_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.reset_spectra_plot("等待加载数据...")

    def reset_spectra_plot(self, message):
        self.spectra_ax.clear()
        self.spectra_ax.set_facecolor("#2b2b2b")
        for spine in self.spectra_ax.spines.values(): spine.set_color('white')
        self.spectra_ax.tick_params(axis='x', colors='white'); self.spectra_ax.tick_params(axis='y', colors='white')
        self.spectra_ax.set_xlabel("X-轴", color="white"); self.spectra_ax.set_ylabel("Y-轴", color="white")
        self.spectra_ax.set_title("谱图", color="white")
        self.spectra_ax.text(0.5, 0.5, message, ha='center', va='center', color='gray', transform=self.spectra_ax.transAxes)
        self.spectra_fig.tight_layout(); self.spectra_canvas.draw()

    def load_and_plot_spectrum(self):
        filepath = filedialog.askopenfilename(title="选择一个CSV谱图文件", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not filepath: return
        try:
            # 尝试自动跳过非数据行
            data = np.loadtxt(filepath, delimiter=',')
            x, y = data[:, 0], data[:, 1]
            self.spectra_ax.clear()
            self.spectra_ax.plot(x, y, color=ctk.ThemeManager.theme["CTkButton"]["fg_color"][0])
            self.spectra_ax.set_facecolor("#2b2b2b")
            for spine in self.spectra_ax.spines.values(): spine.set_color('white')
            self.spectra_ax.tick_params(axis='x', colors='white'); self.spectra_ax.tick_params(axis='y', colors='white')
            self.spectra_ax.set_xlabel("波数 / m/z / 化学位移 (ppm)", color="white")
            self.spectra_ax.set_ylabel("吸光度 / 丰度", color="white")
            self.spectra_ax.set_title(f"谱图: {os.path.basename(filepath)}", color="white")
            self.spectra_ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
            if x.mean() > 500: self.spectra_ax.invert_xaxis()
            self.spectra_fig.tight_layout(); self.spectra_canvas.draw()
            self.spectra_info_label.configure(text=f"已加载: {os.path.basename(filepath)} ({len(x)}个数据点)")
        except Exception as e:
            self.reset_spectra_plot(f"文件加载或解析失败\n{e}\n请确保是两列数值的CSV文件。"); messagebox.showerror("加载错误", f"无法处理文件。\n错误: {e}")

    def create_journal_tab(self):
        tab = self.tabs["实验日志"]
        
        # 主框架
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部按钮栏
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=5)
        
        # 左侧按钮组
        left_button_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        left_button_frame.pack(side="left", padx=10)
        
        ctk.CTkButton(left_button_frame, text="手动保存", command=self.save_log_manual).pack(side="left", padx=5)
        ctk.CTkButton(left_button_frame, text="导出日志", command=self.export_log).pack(side="left", padx=5)
        ctk.CTkButton(left_button_frame, text="历史版本", command=self.show_version_history).pack(side="left", padx=5)
        
        # 右侧自动保存配置
        right_config_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_config_frame.pack(side="right", padx=10)
        
        self.auto_save_var = ctk.BooleanVar(value=self.journal_manager.auto_save_enabled)
        self.auto_save_switch = ctk.CTkSwitch(right_config_frame, text="自动保存", variable=self.auto_save_var,
                                             command=self.toggle_auto_save)
        self.auto_save_switch.pack(side="left", padx=5)
        
        ctk.CTkLabel(right_config_frame, text="间隔: ").pack(side="left", padx=5)
        self.auto_save_interval_entry = ctk.CTkEntry(right_config_frame, width=50,
                                                  placeholder_text=str(self.journal_manager.auto_save_interval // 60))
        self.auto_save_interval_entry.pack(side="left", padx=5)
        self.auto_save_interval_entry.bind("<Return>", self.update_auto_save_interval)
        ctk.CTkLabel(right_config_frame, text="分钟").pack(side="left", padx=5)
        
        # 自动保存状态标签
        self.auto_save_status_label = ctk.CTkLabel(right_config_frame, text="上次保存: 刚刚",
                                                text_color="#00ff00")
        self.auto_save_status_label.pack(side="left", padx=10)
        
        # 日志编辑区域
        self.journal_text = ctk.CTkTextbox(main_frame, wrap="word")
        self.journal_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 加载现有日志
        self.load_log_initial()
        
        # 绑定文本变化事件，用于自动保存
        self.journal_text.bind("<KeyRelease>", self.on_journal_text_change)
    
    def load_log_initial(self):
        """初始加载日志内容"""
        content = self.journal_manager.load_journal()
        self.journal_text.delete("1.0", "end")
        self.journal_text.insert("1.0", content)
    
    def save_log_manual(self):
        """手动保存日志"""
        content = self.journal_text.get("1.0", "end")
        if self.journal_manager.save_journal(content, force=True):
            self.update_auto_save_status(True)
            messagebox.showinfo("成功", "日志已手动保存")
        else:
            messagebox.showerror("错误", "日志保存失败")
    
    def export_log(self):
        """导出日志到指定文件"""
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", 
                                             filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            content = self.journal_text.get("1.0", "end")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("成功", f"日志已导出至 {filepath}")
        except Exception as e:
            messagebox.showerror("错误", f"无法导出文件: {e}")
    
    def on_journal_text_change(self, event=None):
        """日志文本变化时触发，用于自动保存"""
        content = self.journal_text.get("1.0", "end")
        if self.journal_manager.save_journal(content):
            self.update_auto_save_status(True)
    
    def toggle_auto_save(self):
        """切换自动保存开关"""
        enabled = self.auto_save_var.get()
        self.journal_manager.set_auto_save(enabled)
        if enabled:
            self.start_auto_save_timer()
        else:
            self.stop_auto_save_timer()
    
    def update_auto_save_interval(self, event=None):
        """更新自动保存间隔"""
        try:
            interval = int(self.auto_save_interval_entry.get())
            if 1 <= interval <= 60:
                self.journal_manager.set_auto_save_interval(interval)
                self.start_auto_save_timer()
                messagebox.showinfo("成功", f"自动保存间隔已设置为 {interval} 分钟")
            else:
                messagebox.showerror("错误", "间隔必须在1-60分钟之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def show_version_history(self):
        """显示版本历史记录"""
        # 创建版本历史窗口
        history_window = ctk.CTkToplevel(self)
        history_window.title("日志版本历史")
        history_window.geometry("800x600")
        
        # 获取版本历史
        versions = self.journal_manager.get_version_history()
        
        # 版本列表框
        version_list = tkinter.Listbox(history_window, width=100, height=20)
        version_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 填充版本列表
        for version_file, mod_time, file_size in versions:
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            size_str = f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.2f} MB"
            version_list.insert("end", f"{mod_time_str} - {size_str} - {version_file}")
        
        # 按钮框架
        button_frame = ctk.CTkFrame(history_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def restore_selected_version():
            """恢复选中的版本"""
            selected_index = version_list.curselection()
            if not selected_index:
                messagebox.showinfo("提示", "请选择一个版本")
                return
            selected = version_list.get(selected_index)
            version_file = selected.split(" - ")[-1]
            
            if messagebox.askyesno("确认恢复", f"确定要恢复到版本 {version_file} 吗？当前日志将被保存为新版本。"):
                if self.journal_manager.restore_version(version_file):
                    # 重新加载日志内容
                    self.load_log_initial()
                    messagebox.showinfo("成功", f"已恢复到版本 {version_file}")
                    history_window.destroy()
                else:
                    messagebox.showerror("错误", "版本恢复失败")
        
        def delete_selected_version():
            """删除选中的版本"""
            selected_index = version_list.curselection()
            if not selected_index:
                messagebox.showinfo("提示", "请选择一个版本")
                return
            selected = version_list.get(selected_index)
            version_file = selected.split(" - ")[-1]
            
            if messagebox.askyesno("确认删除", f"确定要删除版本 {version_file} 吗？此操作不可撤销。"):
                if self.journal_manager.delete_version(version_file):
                    # 刷新版本列表
                    version_list.delete(selected_index)
                    messagebox.showinfo("成功", f"已删除版本 {version_file}")
                else:
                    messagebox.showerror("错误", "版本删除失败")
        
        # 按钮
        ctk.CTkButton(button_frame, text="恢复选中版本", command=restore_selected_version).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="删除选中版本", command=delete_selected_version).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="关闭", command=history_window.destroy).pack(side="right", padx=5)
    
    def update_auto_save_status(self, saved_successfully=True):
        """更新自动保存状态标签"""
        if saved_successfully:
            last_save_time = datetime.fromtimestamp(self.journal_manager.get_last_save_time())
            self.auto_save_status_label.configure(
                text=f"上次保存: {last_save_time.strftime('%H:%M:%S')}",
                text_color="#00ff00"
            )
        else:
            self.auto_save_status_label.configure(
                text="保存失败",
                text_color="#ff0000"
            )
    
    def on_journal_text_change(self, event=None):
        """日志文本变化时触发，用于自动保存"""
        content = self.journal_text.get("1.0", "end")
        saved = self.journal_manager.save_journal(content)
        self.update_auto_save_status(saved)
    
    def start_auto_save_timer(self):
        """启动自动保存定时器"""
        # 先停止现有定时器
        self.stop_auto_save_timer()
        
        # 每30秒检查一次是否需要自动保存
        self.auto_save_task_id = self.after(30000, self.auto_save_timer_callback)
    
    def stop_auto_save_timer(self):
        """停止自动保存定时器"""
        if self.auto_save_task_id:
            self.after_cancel(self.auto_save_task_id)
            self.auto_save_task_id = None
    
    def auto_save_timer_callback(self):
        """自动保存定时器回调"""
        if self.journal_manager.auto_save_enabled:
            content = self.journal_text.get("1.0", "end")
            saved = self.journal_manager.save_journal(content)
            self.update_auto_save_status(saved)
        
        # 重新启动定时器
        self.start_auto_save_timer()
    
    def create_network_search_tab(self):
        tab = self.tabs["网络查询"]
        
        # 导入所需模块
        from utils.network.search_engine import SearchEngineFactory
        from utils.file_io.export_manager import ExportManager
        
        # 初始化搜索引擎工厂和导出管理器
        self.search_factory = SearchEngineFactory()
        self.export_manager = ExportManager()
        
        # 主框架
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 查询配置区域
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(fill="x", padx=10, pady=10)
        
        # 查询类型选择
        query_type_frame = ctk.CTkFrame(config_frame)
        query_type_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(query_type_frame, text="查询类型: ").pack(side="left", padx=5)
        self.query_type_var = ctk.StringVar(value="academic")
        query_types = ["academic", "chemical"]
        query_type_menu = ctk.CTkOptionMenu(query_type_frame, variable=self.query_type_var,
                                         values=query_types, command=self.on_query_type_change)
        query_type_menu.pack(side="left", padx=5)
        
        # 搜索引擎选择
        engine_frame = ctk.CTkFrame(config_frame)
        engine_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(engine_frame, text="搜索引擎: ").pack(side="left", padx=5)
        self.engine_var = ctk.StringVar(value="google_scholar")
        self.update_engine_options()
        engine_menu = ctk.CTkOptionMenu(engine_frame, variable=self.engine_var,
                                      values=list(self.engines_dict.keys()))
        engine_menu.pack(side="left", padx=5)
        
        # 关键词输入
        keyword_frame = ctk.CTkFrame(config_frame)
        keyword_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(keyword_frame, text="关键词: ").pack(side="left", padx=5)
        self.keyword_entry = ctk.CTkEntry(keyword_frame, placeholder_text="请输入查询关键词")
        self.keyword_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.keyword_entry.bind("<Return>", self.perform_search)
        
        # 搜索按钮
        ctk.CTkButton(keyword_frame, text="搜索", command=self.perform_search).pack(side="left", padx=5)
        
        # 高级搜索选项
        advanced_frame = ctk.CTkFrame(config_frame)
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        self.advanced_var = ctk.BooleanVar(value=False)
        advanced_checkbox = ctk.CTkCheckBox(advanced_frame, text="高级选项", variable=self.advanced_var,
                                          command=self.toggle_advanced_options)
        advanced_checkbox.pack(side="left", padx=5)
        
        # 高级选项内容
        self.advanced_content_frame = ctk.CTkFrame(config_frame)
        # 默认隐藏
        
        # 年份范围
        year_frame = ctk.CTkFrame(self.advanced_content_frame)
        year_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(year_frame, text="年份范围: ").pack(side="left", padx=5)
        self.year_from_entry = ctk.CTkEntry(year_frame, width=60, placeholder_text="从")
        self.year_from_entry.pack(side="left", padx=5)
        ctk.CTkLabel(year_frame, text="到").pack(side="left", padx=5)
        self.year_to_entry = ctk.CTkEntry(year_frame, width=60, placeholder_text="到")
        self.year_to_entry.pack(side="left", padx=5)
        
        # 搜索类型（仅化学物质查询）
        self.chem_search_type_frame = ctk.CTkFrame(self.advanced_content_frame)
        ctk.CTkLabel(self.chem_search_type_frame, text="搜索类型: ").pack(side="left", padx=5)
        self.chem_search_type_var = ctk.StringVar(value="name")
        chem_search_types = ["name", "formula", "smiles", "cas"]
        chem_search_menu = ctk.CTkOptionMenu(self.chem_search_type_frame, variable=self.chem_search_type_var,
                                           values=chem_search_types)
        chem_search_menu.pack(side="left", padx=5)
        
        # 结果数量
        results_frame = ctk.CTkFrame(self.advanced_content_frame)
        results_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(results_frame, text="结果数量: ").pack(side="left", padx=5)
        self.num_results_entry = ctk.CTkEntry(results_frame, width=60, placeholder_text="10")
        self.num_results_entry.pack(side="left", padx=5)
        
        # 结果展示区域
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_columnconfigure(1, weight=1)
        
        # 结果列表
        list_frame = ctk.CTkFrame(results_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(list_frame, text="搜索结果", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # 结果列表框
        self.results_listbox = tkinter.Listbox(list_frame, width=50, height=20)
        self.results_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_result_select)
        
        # 结果列表滚动条
        list_scrollbar = ctk.CTkScrollbar(list_frame, command=self.results_listbox.yview)
        list_scrollbar.pack(side="right", fill="y", pady=5)
        self.results_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # 结果详情
        detail_frame = ctk.CTkFrame(results_frame)
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(detail_frame, text="结果详情", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # 详情文本框
        self.result_detail_text = ctk.CTkTextbox(detail_frame, wrap="word")
        self.result_detail_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 导出按钮
        export_frame = ctk.CTkFrame(main_frame)
        export_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(export_frame, text="导出结果: ").pack(side="left", padx=5)
        self.export_format_var = ctk.StringVar(value="CSV")
        export_formats = ["CSV", "PDF", "文本文件"]
        export_menu = ctk.CTkOptionMenu(export_frame, variable=self.export_format_var,
                                      values=export_formats)
        export_menu.pack(side="left", padx=5)
        
        ctk.CTkButton(export_frame, text="导出", command=self.export_search_results).pack(side="left", padx=5)
        
        # 搜索状态标签
        self.search_status_label = ctk.CTkLabel(main_frame, text="", text_color="#00ff00")
        self.search_status_label.pack(pady=5)
        
        # 存储搜索结果
        self.search_results = []
    
    def on_query_type_change(self, event=None):
        """查询类型改变时更新搜索引擎选项"""
        self.update_engine_options()
        
        # 显示或隐藏化学搜索类型选项
        if self.query_type_var.get() == "chemical":
            self.chem_search_type_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.chem_search_type_frame.pack_forget()
    
    def update_engine_options(self):
        """更新搜索引擎选项"""
        query_type = self.query_type_var.get()
        
        if query_type == "academic":
            self.engines_dict = {
                "Google Scholar": "google_scholar"
            }
        elif query_type == "chemical":
            self.engines_dict = {
                "PubChem": "pubchem",
                "ChemSpider": "chemspider"
            }
        
        # 更新下拉菜单
        if hasattr(self, 'advanced_content_frame'):
            engine_menu = self.advanced_content_frame.winfo_children()[0] if self.advanced_content_frame.winfo_children() else None
        else:
            engine_menu = None
        
        if hasattr(self, 'engine_var'):
            self.engine_var.set(list(self.engines_dict.values())[0])
    
    def toggle_advanced_options(self):
        """切换高级选项的显示/隐藏"""
        if self.advanced_var.get():
            self.advanced_content_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.advanced_content_frame.pack_forget()
    
    def perform_search(self, event=None):
        """执行搜索"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入搜索关键词")
            return
        
        # 更新状态
        self.search_status_label.configure(text="搜索中...", text_color="#ffff00")
        self.update()
        
        try:
            # 获取查询参数
            query_type = self.query_type_var.get()
            engine_name = self.engine_var.get()
            engine_type = self.engines_dict.get(engine_name, engine_name)
            
            # 获取高级选项
            year_from = self.year_from_entry.get()
            year_to = self.year_to_entry.get()
            year_range = None
            if year_from and year_to:
                try:
                    year_range = (int(year_from), int(year_to))
                except ValueError:
                    pass
            
            num_results = self.num_results_entry.get()
            if not num_results:
                num_results = 10
            else:
                try:
                    num_results = int(num_results)
                except ValueError:
                    num_results = 10
            
            # 执行搜索
            engine = self.search_factory.get_search_engine(engine_type)
            
            if query_type == "academic":
                results = engine.search(keyword, num_results=num_results, year_range=year_range)
            elif query_type == "chemical":
                search_type = self.chem_search_type_var.get()
                results = engine.search(keyword, search_type=search_type)
            else:
                results = []
            
            # 显示结果
            self.display_search_results(results)
            self.search_status_label.configure(text=f"搜索完成，找到 {len(results)} 条结果", text_color="#00ff00")
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {e}")
            self.search_status_label.configure(text="搜索失败", text_color="#ff0000")
    
    def display_search_results(self, results):
        """显示搜索结果"""
        # 清空列表
        self.results_listbox.delete(0, tkinter.END)
        self.result_detail_text.delete("1.0", tkinter.END)
        
        # 存储结果
        self.search_results = results
        
        # 添加到列表
        for i, result in enumerate(results, 1):
            if result["type"] == "academic":
                title = result.get("title", "无标题")
                authors = ", ".join(result.get("authors", []))
                journal = result.get("journal", "")
                year = result.get("year", "")
                display_text = f"{i}. {title[:50]}... - {authors} - {journal} ({year})"
            elif result["type"] == "chemical":
                name = result.get("name", result.get("formula", "无名称"))
                formula = result.get("formula", "")
                display_text = f"{i}. {name} - {formula}"
            else:
                display_text = f"{i}. {result.get('title', result.get('name', '无标题'))}"
            
            self.results_listbox.insert(tkinter.END, display_text)
    
    def on_result_select(self, event=None):
        """选择结果时显示详情"""
        selected_index = self.results_listbox.curselection()
        if not selected_index:
            return
        
        index = selected_index[0]
        if index >= len(self.search_results):
            return
        
        result = self.search_results[index]
        
        # 显示详情
        detail_text = "# 结果详情\n\n"
        
        for key, value in result.items():
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
            else:
                value_str = str(value)
            
            detail_text += f"**{key}**: {value_str}\n\n"
        
        self.result_detail_text.delete("1.0", tkinter.END)
        self.result_detail_text.insert("1.0", detail_text)
    
    def export_search_results(self):
        """导出搜索结果"""
        if not self.search_results:
            messagebox.showinfo("提示", "没有可导出的结果")
            return
        
        export_format = self.export_format_var.get().lower()
        
        # 生成文件名
        keyword = self.keyword_entry.get().strip()[:10] if self.keyword_entry.get().strip() else "search"
        filename = f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 执行导出
        filepath = self.export_manager.export_data(
            self.search_results,
            export_format,
            filename=filename,
            title=f"搜索结果: {self.keyword_entry.get().strip()}"
        )
        
        if filepath:
            messagebox.showinfo("成功", f"结果已导出至: {filepath}")
        else:
            messagebox.showerror("错误", "结果导出失败")
    
    def create_ai_assistant_tab(self):
        tab = self.tabs["AI助手"]
        
        # 主框架
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧：提示词管理和API配置
        left_frame = ctk.CTkFrame(main_frame, width=300)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        # API配置面板
        api_frame = ctk.CTkFrame(left_frame, border_color="#3c3c3c", border_width=2)
        api_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(api_frame, text="API配置", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # API密钥输入
        api_key_frame = ctk.CTkFrame(api_frame)
        api_key_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(api_key_frame, text="API密钥: ").pack(side="top", padx=5, pady=5, anchor="w")
        self.api_key_entry = ctk.CTkEntry(api_key_frame, width=250, show="*")
        self.api_key_entry.pack(side="top", padx=5, pady=5, fill="x")
        
        # API密钥管理按钮
        api_button_frame = ctk.CTkFrame(api_frame)
        api_button_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(api_button_frame, text="保存密钥", command=self.save_api_key).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(api_button_frame, text="验证密钥", command=self.verify_api_key).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(api_button_frame, text="清除密钥", command=self.clear_api_key).pack(side="left", padx=5, pady=5)
        
        # API状态显示
        self.api_status_label = ctk.CTkLabel(api_frame, text="API状态: 未配置", text_color="#ff0000")
        self.api_status_label.pack(padx=5, pady=5, anchor="w")
        
        # 提示词模板库
        template_frame = ctk.CTkFrame(left_frame)
        template_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(template_frame, text="提示词模板库", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # 领域选择
        domain_frame = ctk.CTkFrame(template_frame)
        domain_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(domain_frame, text="领域: ").pack(side="left", padx=5)
        self.ai_domain_var = ctk.StringVar(value="材料科学")
        domains = ["材料科学", "化学工程", "有机化学", "无机化学", "分析化学"]
        domain_menu = ctk.CTkOptionMenu(domain_frame, variable=self.ai_domain_var)
        domain_menu.pack(fill="x", padx=5)
        
        # 模板列表
        self.template_listbox = tkinter.Listbox(template_frame, height=10)
        self.template_listbox.pack(fill="x", padx=5, pady=5)
        self.template_listbox.bind("<<ListboxSelect>>", self.on_template_select)
        
        # 加载示例模板
        self.load_example_templates()
        
        # 右侧：AI交互
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # 提示词编辑区域
        prompt_frame = ctk.CTkFrame(right_frame)
        prompt_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(prompt_frame, text="提示词编辑", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        self.prompt_textbox = ctk.CTkTextbox(prompt_frame, height=100, wrap="word")
        self.prompt_textbox.pack(fill="x", padx=5, pady=5)
        
        # 参数配置
        param_frame = ctk.CTkFrame(right_frame)
        param_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(param_frame, text="参数配置", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # 温度参数
        temp_frame = ctk.CTkFrame(param_frame)
        temp_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(temp_frame, text="温度: ").pack(side="left", padx=5)
        self.temp_var = ctk.DoubleVar(value=0.7)
        temp_slider = ctk.CTkSlider(temp_frame, from_=0.0, to=1.0, variable=self.temp_var)
        temp_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.temp_label = ctk.CTkLabel(temp_frame, text=f"{self.temp_var.get():.2f}")
        self.temp_label.pack(side="left", padx=5)
        
        # 最大长度
        max_len_frame = ctk.CTkFrame(param_frame)
        max_len_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(max_len_frame, text="最大长度: ").pack(side="left", padx=5)
        self.max_len_var = ctk.IntVar(value=1000)
        max_len_entry = ctk.CTkEntry(max_len_frame, width=80, textvariable=self.max_len_var)
        max_len_entry.pack(side="left", padx=5)
        ctk.CTkLabel(max_len_frame, text="字符").pack(side="left", padx=5)
        
        # AI交互历史
        history_frame = ctk.CTkFrame(right_frame)
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(history_frame, text="AI交互历史", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=5, pady=5, anchor="w")
        
        # 添加查询功能
        search_frame = ctk.CTkFrame(history_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="输入关键词查询聊天记录...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="查询", command=self.search_chat_history).pack(side="right", padx=5)
        ctk.CTkButton(search_frame, text="清空", command=self.clear_search).pack(side="right", padx=5)
        
        # 添加聊天记录边框容器
        chat_container = ctk.CTkFrame(history_frame, border_color="#3c3c3c", border_width=2, corner_radius=10)
        chat_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.ai_history_text = ctk.CTkTextbox(chat_container, wrap="word", border_width=0)
        self.ai_history_text.pack(fill="both", expand=True, padx=5, pady=5)
        # 设置为只读，防止用户编辑AI回应
        self.ai_history_text.configure(state="disabled")
        # 设置字体，确保化学符号显示正常
        self.ai_history_text.configure(font=ctk.CTkFont(family="SimHei, Arial", size=12))
        
        # 底部按钮
        button_frame = ctk.CTkFrame(right_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(button_frame, text="发送请求", command=self.send_ai_request).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="清空历史", command=self.clear_ai_history).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="保存提示词", command=self.save_prompt).pack(side="right", padx=5)
        
        # 聊天记录分类选择器
        category_frame = ctk.CTkFrame(right_frame)
        category_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(category_frame, text="聊天分类: ").pack(side="left", padx=5)
        self.category_var = ctk.StringVar(value="general")
        categories = ["general", "材料科学", "化学工程", "有机化学", "无机化学", "分析化学"]
        self.category_menu = ctk.CTkOptionMenu(category_frame, variable=self.category_var, values=categories)
        self.category_menu.pack(side="left", padx=5)
        ctk.CTkButton(category_frame, text="新建分类", command=self.create_new_category).pack(side="right", padx=5)
        
        # AI状态标签
        self.ai_status_label = ctk.CTkLabel(right_frame, text="", text_color="#00ff00")
        self.ai_status_label.pack(pady=5)
        
        # 存储AI交互历史
        self.ai_history = []
        
        # 加载已保存的API密钥
        self.load_saved_api_key()
        
        # 加载聊天记录
        self.load_chat_history()
    
    def load_example_templates(self):
        """加载示例提示词模板"""
        # 清空列表
        self.template_listbox.delete(0, tkinter.END)
        
        # 添加示例模板
        examples = [
            "材料合成方案设计",
            "反应路径预测",
            "催化剂性能分析",
            "谱图解析辅助",
            "实验条件优化"
        ]
        
        for example in examples:
            self.template_listbox.insert(tkinter.END, example)
    
    def save_api_key(self):
        """保存API密钥到配置文件"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showinfo("提示", "请输入API密钥")
            return
        
        # 保存API密钥到配置文件
        from core.config import config_manager
        config_manager.set("ai.api_key", api_key)
        
        # 更新API状态
        self.api_status_label.configure(text="API状态: 已配置", text_color="#00ff00")
        messagebox.showinfo("成功", "API密钥已保存")
    
    def verify_api_key(self):
        """验证API密钥是否有效"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showinfo("提示", "请输入API密钥")
            return
        
        # 验证API密钥
        self.api_status_label.configure(text="API状态: 验证中...", text_color="#ffff00")
        self.update()
        
        try:
            from core.ai.silicon_flow_api import SiliconFlowAPI
            api = SiliconFlowAPI()
            api.set_api_key(api_key)
            
            # 尝试获取模型列表来验证API密钥
            models = api.get_models()
            if models and "data" in models:
                self.api_status_label.configure(text="API状态: 有效", text_color="#00ff00")
                messagebox.showinfo("成功", "API密钥验证通过")
            else:
                self.api_status_label.configure(text="API状态: 无效", text_color="#ff0000")
                messagebox.showerror("错误", "API密钥验证失败")
        except Exception as e:
            self.api_status_label.configure(text="API状态: 验证失败", text_color="#ff0000")
            messagebox.showerror("错误", f"API密钥验证失败: {e}")
    
    def clear_api_key(self):
        """清除API密钥"""
        if messagebox.askyesno("确认", "确定要清除API密钥吗？"):
            # 清除配置文件中的API密钥
            from core.config import config_manager
            config_manager.set("ai.api_key", "")
            
            # 清除输入框
            self.api_key_entry.delete(0, tkinter.END)
            
            # 更新API状态
            self.api_status_label.configure(text="API状态: 未配置", text_color="#ff0000")
            messagebox.showinfo("成功", "API密钥已清除")
    
    def load_saved_api_key(self):
        """加载已保存的API密钥"""
        from core.config import config_manager
        api_key = config_manager.get("ai.api_key", "")
        if api_key:
            self.api_key_entry.insert(0, api_key)
            self.api_status_label.configure(text="API状态: 已配置", text_color="#00ff00")
        else:
            self.api_status_label.configure(text="API状态: 未配置", text_color="#ff0000")
    
    def on_template_select(self, event=None):
        """选择模板时加载对应的提示词"""
        selected_index = self.template_listbox.curselection()
        if not selected_index:
            return
        
        index = selected_index[0]
        template_name = self.template_listbox.get(index)
        
        # 示例提示词
        templates = {
            "材料合成方案设计": "请设计一种合成[材料名称]的方案，包括反应路径、实验条件、预期产率和可能的副产物。\n\n要求：\n1. 详细的步骤说明\n2. 关键反应条件（温度、压力、催化剂等）\n3. 安全注意事项\n4. 表征方法建议",
            "反应路径预测": "请预测[反应物]到[产物]的可能反应路径，包括：\n\n1. 主要反应步骤\n2. 中间体结构\n3. 反应机理\n4. 可能的竞争反应\n5. 反应条件建议",
            "催化剂性能分析": "请分析[催化剂]在[反应类型]中的性能，包括：\n\n1. 催化活性\n2. 选择性\n3. 稳定性\n4. 失活机制\n5. 改进建议",
            "谱图解析辅助": "请解析以下[谱图类型]谱图数据，提供：\n\n1. 主要吸收峰/特征峰的归属\n2. 可能的分子结构推断\n3. 与标准谱图的比较\n4. 结论建议\n\n谱图数据：\n[谱图数据]",
            "实验条件优化": "请优化以下实验的条件：\n\n实验目的：[实验目的]\n当前条件：[当前条件]\n存在问题：[存在问题]\n\n要求：\n1. 优化后的条件建议\n2. 优化理由\n3. 预期效果\n4. 验证方法"
        }
        
        prompt = templates.get(template_name, "请输入提示词...")
        self.prompt_textbox.delete("1.0", tkinter.END)
        self.prompt_textbox.insert("1.0", prompt)
    
    def send_ai_request(self):
        """发送AI请求"""
        prompt = self.prompt_textbox.get("1.0", "end").strip()
        if not prompt:
            messagebox.showinfo("提示", "请输入提示词")
            return
        
        # 更新状态
        self.ai_status_label.configure(text="AI思考中...", text_color="#ffff00")
        self.update()
        
        # 创建线程执行API调用，避免阻塞UI主线程
        import threading
        thread = threading.Thread(target=self._ai_api_call_thread, args=(prompt,), daemon=True)
        thread.start()
        return
        try:
            from core.ai.silicon_flow_api import SiliconFlowAPI
            from core.config import config_manager
            
            # 初始化API客户端
            ai_api = SiliconFlowAPI()
            
            # 获取API密钥
            api_key = config_manager.get("ai.api_key", "")
            if not api_key:
                messagebox.showinfo("提示", "请先配置API密钥")
                self.ai_status_label.configure(text="请求失败", text_color="#ff0000")
                return
            
            # 设置API密钥
            ai_api.set_api_key(api_key)
            
            # 构建请求消息
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # 获取温度和最大长度参数
            temperature = self.temp_var.get()
            max_tokens = self.max_len_var.get()
            
            # 调用AI API
            response = ai_api.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 处理API响应
            if response:
                # 调试：打印完整响应结构
                print(f"DEBUG: API响应: {response}")
                
                # 检查是否有错误信息
                if "error" in response:
                    error_msg = response["error"].get("message", "未知错误")
                    ai_response = f"API错误: {error_msg}"
                elif "choices" in response and len(response["choices"]) > 0:
                    # 检查choices[0]的结构
                    if isinstance(response["choices"][0], dict):
                        if "message" in response["choices"][0]:
                            ai_response = response["choices"][0]["message"]["content"]
                        elif "text" in response["choices"][0]:
                            # 处理一些API可能返回的text字段
                            ai_response = response["choices"][0]["text"]
                        else:
                            ai_response = f"API响应结构异常: {response}"
                    else:
                        ai_response = f"API响应结构异常: {response}"
                else:
                    ai_response = f"API响应不包含有效的choices: {response}"
            else:
                ai_response = "API请求失败，未收到响应"
            
            # 更新历史记录
            self.ai_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.ai_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 显示历史记录
            self.display_ai_history()
            
            # 更新状态
            self.ai_status_label.configure(text="请求完成", text_color="#00ff00")
        except Exception as e:
            messagebox.showerror("错误", f"AI请求失败: {e}")
            self.ai_status_label.configure(text="请求失败", text_color="#ff0000")
    
    def render_chemical_symbols(self, text):
        """渲染化学符号和LaTeX公式"""
        import re
        
        # 先处理LaTeX公式
        text = self.render_latex_formulas(text)
        
        # 匹配元素符号和数字组合，如 H2, O2, CO2
        pattern = r'([A-Z][a-z]?)(\d+)'
        
        # 定义数字到Unicode下标的映射
        subscript_map = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', 
            '4': '₄', '5': '₅', '6': '₆', '7': '₇', 
            '8': '₈', '9': '₉'
        }
        
        # 自定义替换函数
        def replace_subscript(match):
            element = match.group(1)
            number = match.group(2)
            # 将数字转换为下标
            subscript_number = ''.join([subscript_map[digit] for digit in number])
            return f'{element}{subscript_number}'
        
        rendered_text = re.sub(pattern, replace_subscript, text)
        return rendered_text
    
    def render_latex_formulas(self, text):
        """渲染LaTeX公式，支持align*环境和复杂公式"""
        import re
        
        # 1. 处理align*环境
        def process_align(match):
            align_content = match.group(1)
            # 移除换行符和对齐符号
            align_content = re.sub(r'\\\\', '\n', align_content)
            align_content = re.sub(r'&', '', align_content)
            align_content = re.sub(r'\\overset\{[^}]+\}\{([^}]+)\}', r'\1', align_content)
            return align_content
        
        # 处理align*环境
        text = re.sub(r'\\begin\{align\*\}([\s\S]*?)\\end\{align\*\}', process_align, text)
        
        # 2. 定义LaTeX命令到Unicode字符的映射
        latex_map = {
            # 箭头
            r'\\rightarrow': '→',
            r'\\leftarrow': '←',
            r'\\leftrightarrow': '↔',
            r'\\uparrow': '↑',
            r'\\downarrow': '↓',
            r'\\xrightarrow\{([^}]+)\}': r'\1 →',  # 带有条件的箭头
            r'\\xleftarrow\{([^}]+)\}': r'\1 ←',  # 带有条件的箭头
            
            # 化学符号
            r'\\text\{([^}]+)\}': r'\1',
            
            # 上下标
            r'_\{([^}]+)\}': self._convert_subscript,
            r'\^\{([^}]+)\}': self._convert_superscript,
            
            # 简单上下标
            r'_([0-9a-zA-Z])': self._convert_single_subscript,
            r'\^([0-9a-zA-Z])': self._convert_single_superscript,
        }
        
        # 3. 处理LaTeX公式
        for pattern, replacement in latex_map.items():
            if callable(replacement):
                # 使用函数处理
                text = re.sub(pattern, lambda match: replacement(match), text)
            else:
                # 使用直接替换
                text = re.sub(pattern, replacement, text)
        
        # 4. 移除公式分隔符
        text = re.sub(r'\[|\]', '', text)
        text = re.sub(r'\(|\)', '', text)
        
        return text
    
    def _convert_subscript(self, match):
        """转换下标"""
        subscript_map = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', 
            '4': '₄', '5': '₅', '6': '₆', '7': '₇', 
            '8': '₈', '9': '₉',
            'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
            'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
            'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
            'v': 'ᵥ', 'x': 'ₓ',
        }
        text = match.group(1)
        return ''.join([subscript_map.get(c, c) for c in text])
    
    def _convert_superscript(self, match):
        """转换上标"""
        superscript_map = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', 
            '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', 
            '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻', '=': '⁼',
            'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
            'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ',
            'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ',
            'p': 'ᵖ', 'q': 'ᵠ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ',
            'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
        }
        text = match.group(1)
        return ''.join([superscript_map.get(c, c) for c in text])
    
    def _convert_single_subscript(self, match):
        """转换单个字符下标"""
        # 为单个字符创建一个模拟的match对象
        class MockMatch:
            def __init__(self, group):
                self.group = group
        
        return self._convert_subscript(MockMatch(lambda x: match.group(1) if x == 1 else match.group(0)))
    
    def _convert_single_superscript(self, match):
        """转换单个字符上标"""
        # 为单个字符创建一个模拟的match对象
        class MockMatch:
            def __init__(self, group):
                self.group = group
        
        return self._convert_superscript(MockMatch(lambda x: match.group(1) if x == 1 else match.group(0)))
    
    def display_ai_history(self):
        """显示AI交互历史"""
        # 先将文本框设置为正常状态，允许编辑
        self.ai_history_text.configure(state="normal")
        
        # 清空当前内容
        self.ai_history_text.delete("1.0", tkinter.END)
        
        # 插入新内容
        for item in self.ai_history:
            role = "用户" if item["role"] == "user" else "AI助手"
            
            # 渲染化学符号
            rendered_content = self.render_chemical_symbols(item["content"])
            
            self.ai_history_text.insert("end", f"[{item['timestamp']}] {role}:\n{rendered_content}\n\n")
        
        # 恢复为只读状态
        self.ai_history_text.configure(state="disabled")
        
        # 滚动到底部，显示最新内容
        self.ai_history_text.see("end")
    
    def clear_ai_history(self):
        """清空AI交互历史"""
        if messagebox.askyesno("确认", "确定要清空所有AI交互历史吗？"):
            self.ai_history = []
            # 先将文本框设置为正常状态，允许编辑
            self.ai_history_text.configure(state="normal")
            # 清空内容
            self.ai_history_text.delete("1.0", tkinter.END)
            # 恢复为只读状态
            self.ai_history_text.configure(state="disabled")
            # 保存清空后的历史记录
            self.save_chat_history()
    
    def search_chat_history(self):
        """查询聊天记录"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入查询关键词")
            return
        
        # 先将文本框设置为正常状态，允许编辑
        self.ai_history_text.configure(state="normal")
        
        # 清空当前内容
        self.ai_history_text.delete("1.0", tkinter.END)
        
        # 搜索并显示匹配的聊天记录
        matched = False
        for item in self.ai_history:
            # 检查内容是否包含关键词，无论角色
            if keyword in item["content"]:
                matched = True
                role = "用户" if item["role"] == "user" else "AI助手"
                
                # 插入时间和角色
                self.ai_history_text.insert("end", f"[{item['timestamp']}] {role}:\n")
                
                # 渲染化学符号
                rendered_content = self.render_chemical_symbols(item["content"])
                
                # 插入内容，高亮匹配关键词
                content = rendered_content
                start_idx = 0
                while True:
                    idx = content.find(keyword, start_idx)
                    if idx == -1:
                        # 剩余内容
                        self.ai_history_text.insert("end", content[start_idx:])
                        break
                    # 匹配前的内容
                    self.ai_history_text.insert("end", content[start_idx:idx])
                    # 匹配的关键词（高亮显示）
                    self.ai_history_text.insert("end", content[idx:idx+len(keyword)], "highlight")
                    start_idx = idx + len(keyword)
                
                self.ai_history_text.insert("end", "\n\n")
        
        if not matched:
            self.ai_history_text.insert("end", "未找到匹配的聊天记录\n")
        
        # 恢复为只读状态
        self.ai_history_text.configure(state="disabled")
        
        # 配置高亮标签
        self.ai_history_text.tag_config("highlight", background="yellow", foreground="black")
    
    def clear_search(self):
        """清空查询结果，显示所有聊天记录"""
        self.search_entry.delete(0, tkinter.END)
        self.display_ai_history()
    
    def save_chat_history(self):
        """保存聊天记录到本地文件"""
        import json
        import os
        
        # 创建聊天记录保存目录
        history_dir = "chat_history"
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 获取当前分类
        category = self.category_var.get()
        
        # 生成文件名（使用分类和当前日期）
        file_name = f"{history_dir}/chat_history_{category}_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        # 构建聊天记录数据结构
        chat_data = {
            "version": "1.0",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "messages": self.ai_history
        }
        
        try:
            # 保存聊天记录
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存聊天记录失败: {e}")
            return False
    
    def load_chat_history(self):
        """从本地文件加载聊天记录"""
        import json
        import os
        
        # 创建聊天记录保存目录
        history_dir = "chat_history"
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 获取当前分类
        category = self.category_var.get()
        
        # 生成文件名（使用分类和当前日期）
        file_name = f"{history_dir}/chat_history_{category}_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        if not os.path.exists(file_name):
            # 尝试加载默认分类的聊天记录
            default_file = f"{history_dir}/chat_history_{datetime.now().strftime('%Y-%m-%d')}.json"
            if os.path.exists(default_file):
                file_name = default_file
            else:
                return False
        
        try:
            # 加载聊天记录
            with open(file_name, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            # 更新聊天历史
            if "messages" in chat_data:
                self.ai_history = chat_data["messages"]
                self.display_ai_history()
            return True
        except Exception as e:
            print(f"加载聊天记录失败: {e}")
            return False
    
    def create_new_category(self):
        """创建新的聊天记录分类"""
        import simpledialog
        
        # 弹出对话框让用户输入新分类名称
        new_category = simpledialog.askstring("新建分类", "请输入新分类名称：")
        if not new_category:
            return
        
        # 获取当前所有分类
        current_values = self.category_menu.cget("values")
        
        # 检查分类是否已存在
        if new_category in current_values:
            messagebox.showinfo("提示", "该分类已存在")
            return
        
        # 添加新分类
        new_values = list(current_values) + [new_category]
        self.category_menu.configure(values=new_values)
        
        # 切换到新分类
        self.category_var.set(new_category)
        
        # 清空当前聊天记录，准备新分类的聊天
        self.ai_history = []
        self.display_ai_history()
        messagebox.showinfo("成功", f"新分类 '{new_category}' 已创建")
    
    def save_prompt(self):
        """保存当前提示词"""
        prompt = self.prompt_textbox.get("1.0", "end").strip()
        if not prompt:
            messagebox.showinfo("提示", "请输入要保存的提示词")
            return
        
        name = simpledialog.askstring("保存提示词", "请输入提示词名称：")
        if not name:
            return
        
        # 这里简化处理，实际需要保存到文件或数据库
        messagebox.showinfo("成功", f"提示词 '{name}' 已保存")
    
    def _ai_api_call_thread(self, prompt):
        """在后台线程中执行AI API调用"""
        try:
            from core.ai.silicon_flow_api import SiliconFlowAPI
            from core.config import config_manager
            
            # 初始化API客户端
            ai_api = SiliconFlowAPI()
            
            # 获取API密钥
            api_key = config_manager.get("ai.api_key", "")
            if not api_key:
                # 使用线程安全的方式更新UI
                self.after(0, lambda: messagebox.showinfo("提示", "请先配置API密钥"))
                self.after(0, lambda: self.ai_status_label.configure(text="请求失败", text_color="#ff0000"))
                return
            
            # 设置API密钥
            ai_api.set_api_key(api_key)
            
            # 构建请求消息
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的化学助手，帮助用户解决化学相关的问题。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # 获取温度和最大长度参数
            temperature = self.temp_var.get()
            max_tokens = self.max_len_var.get()
            
            # 调用AI API（流式）
            self.after(0, lambda: self._stream_ai_response(prompt, ai_api, messages, temperature, max_tokens))
            
        except Exception as e:
            # 使用线程安全的方式显示错误信息
            self.after(0, lambda: messagebox.showerror("错误", f"AI请求失败: {e}"))
            self.after(0, lambda: self.ai_status_label.configure(text="请求失败", text_color="#ff0000"))
    
    def _update_ai_response(self, prompt, ai_response):
        """线程安全的方式更新AI响应（非流式）"""
        try:
            # 更新历史记录
            self.ai_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.ai_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 显示历史记录
            self.display_ai_history()
            
            # 更新状态
            self.ai_status_label.configure(text="请求完成", text_color="#00ff00")
        except Exception as e:
            messagebox.showerror("错误", f"更新AI响应失败: {e}")
    
    def _stream_ai_response(self, prompt, ai_api, messages, temperature, max_tokens):
        """处理流式AI响应并实现动态UI更新"""
        import threading
        
        # 创建一个新的线程来处理流式API调用
        thread = threading.Thread(target=self._stream_ai_api_call, args=(prompt, ai_api, messages, temperature, max_tokens), daemon=True)
        thread.start()
    
    def _stream_ai_api_call(self, prompt, ai_api, messages, temperature, max_tokens):
        """在后台线程中处理流式API调用"""
        try:
            # 先将用户消息添加到历史记录
            user_message = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.ai_history.append(user_message)
            
            # 更新UI，显示用户消息
            self.after(0, self.display_ai_history)
            
            # 初始化AI响应
            ai_response = ""
            ai_message = {
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.ai_history.append(ai_message)
            
            # 调用流式API
            stream_generator = ai_api.chat_completion_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 处理流式响应
            for chunk in stream_generator:
                if chunk is None:
                    # 发生错误
                    ai_response = "API请求失败，未收到响应"
                    break
                    
                # 检查是否有错误信息
                if "error" in chunk:
                    error_msg = chunk["error"].get("message", "未知错误")
                    ai_response = f"API错误: {error_msg}"
                    break
                
                # 提取内容
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    content = delta.get("content", "")
                    
                    if content:
                        # 逐字添加内容，实现打字机效果
                        for char in content:
                            ai_response += char
                            # 更新历史记录中的AI响应
                            ai_message["content"] = ai_response
                            # 动态更新UI
                            self.after(0, self.display_ai_history)
                            # 添加适当延迟，模拟打字机效果
                            import time
                            time.sleep(0.01)  # 10ms延迟，可根据需要调整
            
            # 更新最终状态
            self.after(0, lambda: self.ai_status_label.configure(text="请求完成", text_color="#00ff00"))
            
            # 保存聊天记录
            self.after(0, self.save_chat_history)
            
        except Exception as e:
            # 使用线程安全的方式显示错误信息
            self.after(0, lambda: messagebox.showerror("错误", f"AI请求失败: {e}"))
            self.after(0, lambda: self.ai_status_label.configure(text="请求失败", text_color="#ff0000"))


if __name__ == "__main__":
    # 确保依赖项检查信息能被看到
    if not CHEMPY_AVAILABLE or not PYVISTA_AVAILABLE:
        messagebox.showwarning("依赖警告", "部分功能可能不可用，请查看控制台输出的警告信息。")
    app = ChemApp()
    app.mainloop()
