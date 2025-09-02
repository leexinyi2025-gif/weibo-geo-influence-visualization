import unittest
import pandas as pd
import os
from backend.data_loader import read_weibo_excel, filter_data_by_date

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # 创建测试数据
        self.test_data = {
            '经度': [116.3974, 116.3975, 116.3976],
            '纬度': [39.9093, 39.9094, 39.9095],
            '影响分类': [1, 2, 3],
            '发布时间': ['2023-01-01 10:00:00', '2023-01-02 11:00:00', '2023-01-03 12:00:00']
        }
        self.df = pd.DataFrame(self.test_data)
        self.test_file = 'test_data.xlsx'
        self.df.to_excel(self.test_file, index=False)
    
    def tearDown(self):
        # 清理测试文件
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_read_weibo_excel(self):
        df = read_weibo_excel(self.test_file)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertIn('日期', df.columns)
        self.assertIn('小时', df.columns)
    
    def test_filter_data_by_date(self):
        df = read_weibo_excel(self.test_file)
        filtered_df = filter_data_by_date(df, '2023-01-02', '2023-01-02')
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['影响分类'], 2)

if __name__ == '__main__':
    unittest.main()