import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataAnalysisService:
    def __init__(self):
        # Set matplotlib to use non-interactive backend
        plt.switch_backend('Agg')
        sns.set_theme()
        
    def create_visualization(self, data: List[Dict], chart_type: str, x_column: str, y_column: str = None) -> Dict:
        """Create a visualization from data"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            if chart_type == "bar":
                if y_column:
                    plt.bar(df[x_column], df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    df[x_column].value_counts().plot(kind='bar')
                    plt.xlabel(x_column)
                    plt.ylabel('Count')
                    
            elif chart_type == "line":
                if y_column:
                    plt.plot(df[x_column], df[y_column], marker='o')
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    return {"success": False, "error": "Line chart requires both x and y columns"}
                    
            elif chart_type == "scatter":
                if y_column:
                    plt.scatter(df[x_column], df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    return {"success": False, "error": "Scatter plot requires both x and y columns"}
                    
            elif chart_type == "pie":
                if y_column:
                    plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
                else:
                    df[x_column].value_counts().plot(kind='pie', autopct='%1.1f%%')
                    
            else:
                return {"success": False, "error": f"Unsupported chart type: {chart_type}"}
            
            plt.title(f"{chart_type.capitalize()} Chart")
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{image_base64}",
                "chart_type": chart_type
            }
            
        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            plt.close()
            return {"success": False, "error": str(e)}
    
    def analyze_data(self, data: List[Dict]) -> Dict:
        """Perform basic statistical analysis on data"""
        try:
            df = pd.DataFrame(data)
            
            # Get numeric columns
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            
            analysis = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "numeric_columns": numeric_columns,
                "statistics": {}
            }
            
            # Calculate statistics for numeric columns
            for col in numeric_columns:
                analysis["statistics"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "null_count": int(df[col].isnull().sum())
                }
            
            return {"success": True, "analysis": analysis}
            
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {"success": False, "error": str(e)}

# Create singleton instance
data_analysis_service = DataAnalysisService()