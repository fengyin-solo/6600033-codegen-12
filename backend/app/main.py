from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd
from scipy import stats

app = FastAPI(title="Monte Carlo API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root(): return {"service": "Monte Carlo API", "status": "running"}

class DataCleaningRequest(BaseModel):
    data: List[List[Any]]
    columns: List[str]
    missing_value_method: str = "mean"
    outlier_method: str = "iqr"
    outlier_threshold: float = 1.5
    outlier_action: str = "cap"

class ColumnStats(BaseModel):
    name: str
    count: int
    missing_count: int
    missing_percent: float
    mean: Optional[float]
    median: Optional[float]
    std: Optional[float]
    min: Optional[float]
    max: Optional[float]
    outlier_count: Optional[int]
    outlier_percent: Optional[float]

class CleaningResult(BaseModel):
    before: Dict[str, Any]
    after: Dict[str, Any]
    missing_report: Dict[str, Any]
    outlier_report: Dict[str, Any]
    processed_data: List[List[Any]]

def calculate_stats(df: pd.DataFrame, should_detect_outliers: bool = False, 
                    outlier_method: str = "iqr", threshold: float = 1.5) -> Dict[str, Any]:
    stats_dict = {"columns": [], "total_rows": len(df), "total_missing": int(df.isna().sum().sum()), "total_outliers": 0}
    
    for col in df.columns:
        col_data = df[col]
        col_stats = {
            "name": col,
            "count": int(col_data.count()),
            "missing_count": int(col_data.isna().sum()),
            "missing_percent": round(float(col_data.isna().mean() * 100), 2)
        }
        
        if pd.api.types.is_numeric_dtype(col_data):
            col_stats["mean"] = round(float(col_data.mean()), 4) if not col_data.isna().all() else None
            col_stats["median"] = round(float(col_data.median()), 4) if not col_data.isna().all() else None
            col_stats["std"] = round(float(col_data.std()), 4) if not col_data.isna().all() else None
            col_stats["min"] = round(float(col_data.min()), 4) if not col_data.isna().all() else None
            col_stats["max"] = round(float(col_data.max()), 4) if not col_data.isna().all() else None
            
            if should_detect_outliers and col_stats["count"] > 0:
                clean_data = col_data.dropna()
                if len(clean_data) > 0:
                    outliers = detect_outliers_fn(clean_data, outlier_method, threshold)
                    col_stats["outlier_count"] = int(outliers.sum())
                    col_stats["outlier_percent"] = round(float(outliers.sum() / len(clean_data) * 100), 2)
                    stats_dict["total_outliers"] += int(outliers.sum())
                else:
                    col_stats["outlier_count"] = 0
                    col_stats["outlier_percent"] = 0.0
            else:
                col_stats["outlier_count"] = None
                col_stats["outlier_percent"] = None
        else:
            col_stats["mean"] = None
            col_stats["median"] = None
            col_stats["std"] = None
            col_stats["min"] = None
            col_stats["max"] = None
            col_stats["outlier_count"] = None
            col_stats["outlier_percent"] = None
        
        stats_dict["columns"].append(col_stats)
    
    stats_dict["total_missing_percent"] = round(stats_dict["total_missing"] / (len(df) * len(df.columns)) * 100, 2)
    stats_dict["total_outlier_percent"] = round(stats_dict["total_outliers"] / (len(df) * len(df.columns)) * 100, 2) if len(df) > 0 else 0
    
    return stats_dict

def detect_outliers_fn(data: pd.Series, method: str = "iqr", threshold: float = 1.5) -> pd.Series:
    if method == "iqr":
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        return (data < lower_bound) | (data > upper_bound)
    elif method == "zscore":
        z_scores = np.abs(stats.zscore(data))
        return pd.Series(z_scores > threshold, index=data.index)
    else:
        return pd.Series([False] * len(data), index=data.index)

def handle_missing_values(df: pd.DataFrame, method: str) -> pd.DataFrame:
    result = df.copy()
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    
    if method == "mean":
        for col in numeric_cols:
            result[col] = result[col].fillna(result[col].mean())
    elif method == "median":
        for col in numeric_cols:
            result[col] = result[col].fillna(result[col].median())
    elif method == "mode":
        for col in result.columns:
            mode_val = result[col].mode()
            if len(mode_val) > 0:
                result[col] = result[col].fillna(mode_val.iloc[0])
    elif method == "forward":
        result = result.ffill().bfill()
    elif method == "backward":
        result = result.bfill().ffill()
    elif method == "drop":
        result = result.dropna()
    elif method == "zero":
        for col in numeric_cols:
            result[col] = result[col].fillna(0)
    
    return result

def handle_outliers(df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5, action: str = "cap") -> pd.DataFrame:
    result = df.copy()
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        data = result[col].dropna()
        if len(data) == 0:
            continue
            
        outliers = detect_outliers_fn(data, method, threshold)
        if outliers.sum() == 0:
            continue
            
        if method == "iqr":
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
        else:
            mean = data.mean()
            std = data.std()
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std
        
        if action == "cap":
            result.loc[result[col] < lower_bound, col] = lower_bound
            result.loc[result[col] > upper_bound, col] = upper_bound
        elif action == "remove":
            result = result[~((result[col] < lower_bound) | (result[col] > upper_bound))]
        elif action == "mean":
            col_mean = data.mean()
            result.loc[outliers.index[outliers], col] = col_mean
        elif action == "median":
            col_median = data.median()
            result.loc[outliers.index[outliers], col] = col_median
    
    return result

def get_histogram_data(df: pd.DataFrame, column: str, bins: int = 20) -> Dict[str, Any]:
    if column not in df.columns:
        return {"labels": [], "values": []}
    
    data = df[column].dropna()
    if len(data) == 0 or not pd.api.types.is_numeric_dtype(data):
        return {"labels": [], "values": []}
    
    counts, bin_edges = np.histogram(data, bins=bins)
    labels = [f"{round(bin_edges[i], 2)}-{round(bin_edges[i+1], 2)}" for i in range(len(bin_edges)-1)]
    
    return {"labels": labels, "values": counts.tolist()}

def get_boxplot_data(df: pd.DataFrame, column: str) -> Optional[Dict[str, Any]]:
    if column not in df.columns:
        return None
    
    data = df[column].dropna()
    if len(data) == 0 or not pd.api.types.is_numeric_dtype(data):
        return None
    
    q1 = float(data.quantile(0.25))
    q2 = float(data.quantile(0.5))
    q3 = float(data.quantile(0.75))
    iqr = q3 - q1
    min_val = float(data.min())
    max_val = float(data.max())
    
    return {
        "min": round(min_val, 4),
        "q1": round(q1, 4),
        "median": round(q2, 4),
        "q3": round(q3, 4),
        "max": round(max_val, 4),
        "lower_whisker": round(max(min_val, q1 - 1.5 * iqr), 4),
        "upper_whisker": round(min(max_val, q3 + 1.5 * iqr), 4)
    }

@app.post("/api/data-cleaning/analyze", response_model=Dict[str, Any])
def analyze_data(request: DataCleaningRequest):
    df = pd.DataFrame(request.data, columns=request.columns)
    
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass
    
    before_stats = calculate_stats(df, should_detect_outliers=True, 
                                   outlier_method=request.outlier_method, 
                                   threshold=request.outlier_threshold)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    histograms_before = {}
    boxplots_before = {}
    for col in numeric_cols:
        histograms_before[col] = get_histogram_data(df, col)
        boxplots_before[col] = get_boxplot_data(df, col)
    
    df_cleaned = handle_missing_values(df, request.missing_value_method)
    df_cleaned = handle_outliers(df_cleaned, request.outlier_method, 
                                  request.outlier_threshold, request.outlier_action)
    
    after_stats = calculate_stats(df_cleaned, should_detect_outliers=True,
                                  outlier_method=request.outlier_method,
                                  threshold=request.outlier_threshold)
    
    histograms_after = {}
    boxplots_after = {}
    for col in numeric_cols:
        if col in df_cleaned.columns:
            histograms_after[col] = get_histogram_data(df_cleaned, col)
            boxplots_after[col] = get_boxplot_data(df_cleaned, col)
    
    missing_report = {
        "total_missing_before": before_stats["total_missing"],
        "total_missing_after": after_stats["total_missing"],
        "missing_method": request.missing_value_method,
        "columns": []
    }
    
    for col_before in before_stats["columns"]:
        col_after = next((c for c in after_stats["columns"] if c["name"] == col_before["name"]), None)
        if col_after:
            missing_report["columns"].append({
                "name": col_before["name"],
                "missing_before": col_before["missing_count"],
                "missing_after": col_after["missing_count"],
                "missing_percent_before": col_before["missing_percent"],
                "missing_percent_after": col_after["missing_percent"]
            })
    
    outlier_report = {
        "total_outliers_before": before_stats["total_outliers"],
        "total_outliers_after": after_stats["total_outliers"],
        "outlier_method": request.outlier_method,
        "outlier_threshold": request.outlier_threshold,
        "outlier_action": request.outlier_action,
        "columns": []
    }
    
    for col_before in before_stats["columns"]:
        col_after = next((c for c in after_stats["columns"] if c["name"] == col_before["name"]), None)
        if col_after and col_before["outlier_count"] is not None:
            outlier_report["columns"].append({
                "name": col_before["name"],
                "outliers_before": col_before["outlier_count"],
                "outliers_after": col_after["outlier_count"] if col_after["outlier_count"] is not None else 0,
                "outlier_percent_before": col_before["outlier_percent"],
                "outlier_percent_after": col_after["outlier_percent"] if col_after["outlier_percent"] is not None else 0.0
            })
    
    processed_data = df_cleaned.astype(object).where(df_cleaned.notna(), None).values.tolist()
    
    return {
        "before": {
            "stats": before_stats,
            "histograms": histograms_before,
            "boxplots": boxplots_before,
            "data_preview": df.head(10).astype(object).where(df.head(10).notna(), None).values.tolist()
        },
        "after": {
            "stats": after_stats,
            "histograms": histograms_after,
            "boxplots": boxplots_after,
            "data_preview": df_cleaned.head(10).astype(object).where(df_cleaned.head(10).notna(), None).values.tolist()
        },
        "missing_report": missing_report,
        "outlier_report": outlier_report,
        "processed_data": processed_data,
        "columns": request.columns
    }

@app.get("/api/data-cleaning/sample-data")
def get_sample_data():
    np.random.seed(42)
    n = 100
    
    age = np.random.normal(35, 10, n)
    age = np.append(age, [150, 2, np.nan, np.nan])
    
    income = np.random.normal(50000, 15000, n)
    income = np.append(income, [200000, 1000, np.nan, 30000])
    
    score = np.random.normal(75, 15, n)
    score = np.append(score, [150, np.nan, np.nan, 999])
    
    spending = np.random.normal(2000, 500, n)
    spending = np.append(spending, [np.nan, 10000, 50, np.nan])
    
    df = pd.DataFrame({
        "年龄": np.round(age, 1),
        "收入": np.round(income, 2),
        "分数": np.round(score, 1),
        "消费额": np.round(spending, 2)
    })
    
    return {
        "data": df.astype(object).where(df.notna(), None).values.tolist(),
        "columns": df.columns.tolist()
    }
