import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional


class ChartGenerationService:
    """Generates high-resolution chart images for PDF embedding using Matplotlib."""

    def __init__(self):
        # Configure enterprise theme styling
        plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
        plt.rcParams['axes.edgecolor'] = '#CBD5E1'
        plt.rcParams['axes.linewidth'] = 0.8

    def generate_quality_comparison_chart(self, before_score: float, after_score: float) -> bytes:
        """Generates a sleek Before vs After Overall Quality Score comparison bar chart."""
        fig, ax = plt.subplots(figsize=(6, 3), dpi=200)

        labels = ['Before Remediation', 'After Remediation']
        values = [before_score, after_score]
        colors = ['#EF4444' if before_score < 75 else '#F59E0B' if before_score < 90 else '#3B82F6', '#10B981']

        bars = ax.bar(labels, values, color=colors, width=0.45, edgecolor='#1E293B', linewidth=1)

        ax.set_ylim(0, 115)
        ax.set_ylabel('Quality Index (%)', fontsize=9, fontweight='bold', color='#1E293B')
        ax.set_title('Overall Quality Score: Before vs. After', fontsize=11, fontweight='bold', color='#0F172A', pad=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4),  # 4 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold', color='#0F172A')

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_dimension_radar_chart(self, dimensions: List[Dict[str, Any]]) -> bytes:
        """Generates a horizontal grouped bar chart comparing quality dimensions."""
        fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=200)

        names = [d["name"] for d in dimensions]
        before_vals = [d["before"] for d in dimensions]
        after_vals = [d["after"] for d in dimensions]

        y = np.arange(len(names))
        height = 0.35

        rects1 = ax.barh(y - height/2, before_vals, height, label='Before', color='#94A3B8', edgecolor='#475569')
        rects2 = ax.barh(y + height/2, after_vals, height, label='After', color='#3B82F6', edgecolor='#1D4ED8')

        ax.set_xlabel('Score (%)', fontsize=8.5, fontweight='bold', color='#1E293B')
        ax.set_title('Multidimensional Data Quality Breakdown', fontsize=10.5, fontweight='bold', color='#0F172A', pad=10)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8.5, fontweight='bold', color='#1E293B')
        ax.set_xlim(0, 115)
        ax.legend(loc='lower right', fontsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', linestyle='--', alpha=0.5)

        # Add data labels
        for rect in rects2:
            width = rect.get_width()
            ax.annotate(f'{width:.1f}%',
                        xy=(width, rect.get_y() + rect.get_height() / 2),
                        xytext=(4, 0),
                        textcoords="offset points",
                        ha='left', va='center', fontsize=7.5, fontweight='bold', color='#1D4ED8')

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_issue_reduction_chart(self, missing_b: int, missing_a: int, dup_b: int, dup_a: int, fmt_b: int, fmt_a: int, anom_b: int, anom_a: int) -> bytes:
        """Generates a grouped bar chart visualizing issue count reduction."""
        fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=200)

        categories = ['Missing Cells', 'Duplicate Rows', 'Format Errors', 'ML Anomalies']
        before_counts = [missing_b, dup_b, fmt_b, anom_b]
        after_counts = [missing_a, dup_a, fmt_a, anom_a]

        x = np.arange(len(categories))
        width = 0.35

        rects1 = ax.bar(x - width/2, before_counts, width, label='Detected (Before)', color='#EF4444', edgecolor='#991B1B')
        rects2 = ax.bar(x + width/2, after_counts, width, label='Remaining (After)', color='#10B981', edgecolor='#065F46')

        ax.set_ylabel('Defect Count', fontsize=8.5, fontweight='bold', color='#1E293B')
        ax.set_title('Quality Defect Resolution Summary', fontsize=10.5, fontweight='bold', color='#0F172A', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=8, fontweight='bold', color='#1E293B')
        ax.legend(loc='upper right', fontsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Annotate counts on top of bars
        for rect in rects1:
            h = rect.get_height()
            if h > 0:
                ax.annotate(f'{h:,}', xy=(rect.get_x() + rect.get_width() / 2, h),
                            xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7, fontweight='bold', color='#991B1B')

        for rect in rects2:
            h = rect.get_height()
            ax.annotate(f'{h:,}', xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7, fontweight='bold', color='#065F46')

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()


chart_generator = ChartGenerationService()
