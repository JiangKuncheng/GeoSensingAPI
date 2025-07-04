#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoSensingAPI 启动脚本
"""

import sys
import os
import uvicorn

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """启动API服务"""
    print("启动 GeoSensingAPI 服务...")
    print(f"工作目录: {current_dir}")
    print("服务地址: http://127.0.0.1:8000")
    print("API文档: http://127.0.0.1:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "APIversion.allAPI:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 