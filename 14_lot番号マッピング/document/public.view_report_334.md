# view_report_334

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | public                                                                                               |
| 物理テーブル名                 | view_report_334                                                                                      |
| 論理テーブル名                 |                                                                                                      |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/11/14                                                                                           |
| RDBMS                          | PostgreSQL 16.3, compiled by Visual C++ build 1939, 64-bit 16.3                                      |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | rep_top_id                     | integer                        |          |                      |                                |
|   2 |                                | rep_top_name                   | text                           |          |                      |                                |
|   3 |                                | public_status                  | numeric(1)                     |          |                      |                                |
|   4 |                                | edit_refer_status              | numeric(1)                     |          |                      |                                |
|   5 |                                | rep_top_org                    | integer                        |          |                      |                                |
|   6 |                                | rev_no                         | integer                        |          |                      |                                |
|   7 |                                | def_top_id                     | integer                        |          |                      |                                |
|   8 |                                | report_type                    | numeric(1)                     |          |                      |                                |
|   9 |                                | rep_sheet_count                | integer                        |          |                      |                                |
|  10 |                                | display_sheet_number           | text                           |          |                      |                                |
|  11 |                                | server_version                 | text                           |          |                      |                                |
|  12 |                                | top_remarks1                   | text                           |          |                      |                                |
|  13 |                                | top_remarks2                   | text                           |          |                      |                                |
|  14 |                                | top_remarks3                   | text                           |          |                      |                                |
|  15 |                                | top_remarks4                   | text                           |          |                      |                                |
|  16 |                                | top_remarks5                   | text                           |          |                      |                                |
|  17 |                                | top_remarks6                   | text                           |          |                      |                                |
|  18 |                                | top_remarks7                   | text                           |          |                      |                                |
|  19 |                                | top_remarks8                   | text                           |          |                      |                                |
|  20 |                                | top_remarks9                   | text                           |          |                      |                                |
|  21 |                                | top_remarks10                  | text                           |          |                      |                                |
|  22 |                                | sys_regist_term                | text                           |          |                      |                                |
|  23 |                                | sys_regist_user                | text                           |          |                      |                                |
|  24 |                                | sys_regist_time                | timestamp(6) without time zone |          |                      |                                |
|  25 |                                | sys_update_term                | text                           |          |                      |                                |
|  26 |                                | sys_update_user                | text                           |          |                      |                                |
|  27 |                                | sys_update_time                | timestamp(6) without time zone |          |                      |                                |
|  28 |                                | cluster_1_0_t                  | text                           |          |                      |                                |
|  29 |                                | cluster_1_1_t                  | text                           |          |                      |                                |
|  30 |                                | cluster_1_2_t                  | text                           |          |                      |                                |
|  31 |                                | cluster_1_3_t                  | text                           |          |                      |                                |
|  32 |                                | cluster_1_4_t                  | text                           |          |                      |                                |
|  33 |                                | cluster_1_5_t                  | text                           |          |                      |                                |
|  34 |                                | cluster_1_6_t                  | text                           |          |                      |                                |
|  35 |                                | cluster_1_7_t                  | text                           |          |                      |                                |
|  36 |                                | cluster_1_8_t                  | text                           |          |                      |                                |
|  37 |                                | cluster_1_9_t                  | text                           |          |                      |                                |
|  38 |                                | cluster_1_10_t                 | text                           |          |                      |                                |
|  39 |                                | cluster_1_11_t                 | text                           |          |                      |                                |
|  40 |                                | cluster_1_12_t                 | text                           |          |                      |                                |
|  41 |                                | cluster_1_13_t                 | text                           |          |                      |                                |
|  42 |                                | cluster_1_14_t                 | text                           |          |                      |                                |
|  43 |                                | cluster_1_15_t                 | text                           |          |                      |                                |
|  44 |                                | cluster_1_16_t                 | text                           |          |                      |                                |
|  45 |                                | cluster_1_17_t                 | text                           |          |                      |                                |
|  46 |                                | cluster_1_18_t                 | text                           |          |                      |                                |
|  47 |                                | cluster_1_19_t                 | text                           |          |                      |                                |
|  48 |                                | cluster_1_20_t                 | text                           |          |                      |                                |
|  49 |                                | cluster_1_21_n                 | numeric(19, 10)                |          |                      |                                |
|  50 |                                | cluster_1_22_t                 | text                           |          |                      |                                |
|  51 |                                | cluster_1_23_t                 | text                           |          |                      |                                |
|  52 |                                | cluster_1_24_t                 | text                           |          |                      |                                |
|  53 |                                | cluster_1_25_t                 | text                           |          |                      |                                |
|  54 |                                | cluster_1_26_n                 | numeric(19, 10)                |          |                      |                                |
|  55 |                                | cluster_1_27_t                 | text                           |          |                      |                                |
|  56 |                                | cluster_1_28_t                 | text                           |          |                      |                                |
|  57 |                                | cluster_1_29_t                 | text                           |          |                      |                                |
|  58 |                                | cluster_1_30_t                 | text                           |          |                      |                                |
|  59 |                                | cluster_1_31_n                 | numeric(19, 10)                |          |                      |                                |
|  60 |                                | cluster_1_32_t                 | text                           |          |                      |                                |
|  61 |                                | cluster_1_33_t                 | text                           |          |                      |                                |
|  62 |                                | cluster_1_34_t                 | text                           |          |                      |                                |
|  63 |                                | cluster_1_35_t                 | text                           |          |                      |                                |
|  64 |                                | cluster_1_36_t                 | text                           |          |                      |                                |
|  65 |                                | cluster_1_37_n                 | numeric(19, 10)                |          |                      |                                |
|  66 |                                | cluster_1_38_t                 | text                           |          |                      |                                |
|  67 |                                | cluster_1_39_t                 | text                           |          |                      |                                |
|  68 |                                | cluster_1_40_t                 | text                           |          |                      |                                |
|  69 |                                | cluster_1_41_t                 | text                           |          |                      |                                |
|  70 |                                | cluster_1_42_t                 | text                           |          |                      |                                |
|  71 |                                | cluster_1_43_n                 | numeric(19, 10)                |          |                      |                                |
|  72 |                                | cluster_1_44_t                 | text                           |          |                      |                                |
|  73 |                                | cluster_1_45_t                 | text                           |          |                      |                                |
|  74 |                                | cluster_1_46_t                 | text                           |          |                      |                                |
|  75 |                                | cluster_1_47_t                 | text                           |          |                      |                                |
|  76 |                                | cluster_1_48_t                 | text                           |          |                      |                                |
|  77 |                                | cluster_1_49_n                 | numeric(19, 10)                |          |                      |                                |
|  78 |                                | cluster_1_50_t                 | text                           |          |                      |                                |
|  79 |                                | cluster_1_51_t                 | text                           |          |                      |                                |
|  80 |                                | cluster_1_52_t                 | text                           |          |                      |                                |
|  81 |                                | cluster_1_53_t                 | text                           |          |                      |                                |
|  82 |                                | cluster_1_54_t                 | text                           |          |                      |                                |
|  83 |                                | cluster_1_55_n                 | numeric(19, 10)                |          |                      |                                |
|  84 |                                | cluster_1_56_t                 | text                           |          |                      |                                |
|  85 |                                | cluster_1_57_t                 | text                           |          |                      |                                |
|  86 |                                | cluster_1_58_t                 | text                           |          |                      |                                |
|  87 |                                | cluster_1_59_t                 | text                           |          |                      |                                |
|  88 |                                | cluster_1_60_n                 | numeric(19, 10)                |          |                      |                                |
|  89 |                                | cluster_1_61_t                 | text                           |          |                      |                                |
|  90 |                                | cluster_1_62_t                 | text                           |          |                      |                                |
|  91 |                                | cluster_1_63_t                 | text                           |          |                      |                                |
|  92 |                                | cluster_1_64_t                 | text                           |          |                      |                                |
|  93 |                                | cluster_1_65_n                 | numeric(19, 10)                |          |                      |                                |
|  94 |                                | cluster_1_66_t                 | text                           |          |                      |                                |
|  95 |                                | cluster_1_67_t                 | text                           |          |                      |                                |
|  96 |                                | cluster_1_69_t                 | text                           |          |                      |                                |
|  97 |                                | cluster_1_70_n                 | numeric(19, 10)                |          |                      |                                |
|  98 |                                | cluster_1_71_t                 | text                           |          |                      |                                |
|  99 |                                | cluster_1_72_t                 | text                           |          |                      |                                |
| 100 |                                | cluster_1_74_t                 | text                           |          |                      |                                |
| 101 |                                | cluster_1_75_n                 | numeric(19, 10)                |          |                      |                                |
| 102 |                                | cluster_1_76_t                 | text                           |          |                      |                                |
| 103 |                                | cluster_1_77_t                 | text                           |          |                      |                                |
| 104 |                                | cluster_1_78_t                 | text                           |          |                      |                                |
| 105 |                                | cluster_1_79_t                 | text                           |          |                      |                                |
| 106 |                                | cluster_1_80_t                 | text                           |          |                      |                                |
| 107 |                                | cluster_1_81_n                 | numeric(19, 10)                |          |                      |                                |
| 108 |                                | cluster_1_82_t                 | text                           |          |                      |                                |
| 109 |                                | cluster_1_83_t                 | text                           |          |                      |                                |
| 110 |                                | cluster_1_84_t                 | text                           |          |                      |                                |
| 111 |                                | cluster_1_85_t                 | text                           |          |                      |                                |
| 112 |                                | cluster_1_86_t                 | text                           |          |                      |                                |
| 113 |                                | cluster_1_87_n                 | numeric(19, 10)                |          |                      |                                |
| 114 |                                | cluster_1_88_t                 | text                           |          |                      |                                |
| 115 |                                | cluster_1_89_t                 | text                           |          |                      |                                |
| 116 |                                | cluster_1_90_t                 | text                           |          |                      |                                |
| 117 |                                | cluster_1_91_t                 | text                           |          |                      |                                |
| 118 |                                | cluster_1_92_n                 | numeric(19, 10)                |          |                      |                                |
| 119 |                                | cluster_1_93_t                 | text                           |          |                      |                                |
| 120 |                                | cluster_1_94_t                 | text                           |          |                      |                                |
| 121 |                                | cluster_1_95_t                 | text                           |          |                      |                                |
| 122 |                                | cluster_1_96_t                 | text                           |          |                      |                                |
| 123 |                                | cluster_1_97_n                 | numeric(19, 10)                |          |                      |                                |
| 124 |                                | cluster_1_98_t                 | text                           |          |                      |                                |
| 125 |                                | cluster_1_99_t                 | text                           |          |                      |                                |
| 126 |                                | cluster_1_100_t                | text                           |          |                      |                                |
| 127 |                                | cluster_1_101_t                | text                           |          |                      |                                |
| 128 |                                | cluster_1_102_n                | numeric(19, 10)                |          |                      |                                |
| 129 |                                | cluster_1_103_t                | text                           |          |                      |                                |
| 130 |                                | cluster_1_104_t                | text                           |          |                      |                                |
| 131 |                                | cluster_1_105_t                | text                           |          |                      |                                |
| 132 |                                | cluster_1_106_t                | text                           |          |                      |                                |
| 133 |                                | cluster_1_107_n                | numeric(19, 10)                |          |                      |                                |
| 134 |                                | cluster_1_108_t                | text                           |          |                      |                                |
| 135 |                                | cluster_1_109_t                | text                           |          |                      |                                |
| 136 |                                | cluster_1_110_t                | text                           |          |                      |                                |
| 137 |                                | cluster_1_111_t                | text                           |          |                      |                                |
| 138 |                                | cluster_1_112_t                | text                           |          |                      |                                |
| 139 |                                | cluster_1_113_n                | numeric(19, 10)                |          |                      |                                |
| 140 |                                | cluster_1_114_t                | text                           |          |                      |                                |
| 141 |                                | cluster_1_115_t                | text                           |          |                      |                                |
| 142 |                                | cluster_1_116_t                | text                           |          |                      |                                |
| 143 |                                | cluster_1_117_t                | text                           |          |                      |                                |
| 144 |                                | cluster_1_118_n                | numeric(19, 10)                |          |                      |                                |
| 145 |                                | cluster_1_119_t                | text                           |          |                      |                                |
| 146 |                                | cluster_1_120_t                | text                           |          |                      |                                |
| 147 |                                | cluster_1_121_t                | text                           |          |                      |                                |
| 148 |                                | cluster_1_122_t                | text                           |          |                      |                                |
| 149 |                                | cluster_1_123_n                | numeric(19, 10)                |          |                      |                                |
| 150 |                                | cluster_1_124_t                | text                           |          |                      |                                |
| 151 |                                | cluster_1_125_t                | text                           |          |                      |                                |
| 152 |                                | cluster_1_126_t                | text                           |          |                      |                                |
| 153 |                                | cluster_1_127_t                | text                           |          |                      |                                |
| 154 |                                | cluster_1_128_t                | text                           |          |                      |                                |
| 155 |                                | cluster_1_129_n                | numeric(19, 10)                |          |                      |                                |
| 156 |                                | cluster_1_130_t                | text                           |          |                      |                                |
| 157 |                                | cluster_1_131_t                | text                           |          |                      |                                |
| 158 |                                | cluster_1_132_n                | numeric(19, 10)                |          |                      |                                |
| 159 |                                | cluster_1_133_n                | numeric(19, 10)                |          |                      |                                |
| 160 |                                | cluster_1_134_n                | numeric(19, 10)                |          |                      |                                |
| 161 |                                | cluster_1_135_n                | numeric(19, 10)                |          |                      |                                |
| 162 |                                | cluster_1_136_n                | numeric(19, 10)                |          |                      |                                |
| 163 |                                | cluster_1_137_t                | text                           |          |                      |                                |
| 164 |                                | cluster_1_138_t                | text                           |          |                      |                                |
| 165 |                                | cluster_1_139_n                | numeric(19, 10)                |          |                      |                                |
| 166 |                                | cluster_1_140_n                | numeric(19, 10)                |          |                      |                                |
| 167 |                                | cluster_1_141_n                | numeric(19, 10)                |          |                      |                                |
| 168 |                                | cluster_1_142_n                | numeric(19, 10)                |          |                      |                                |
| 169 |                                | cluster_1_143_n                | numeric(19, 10)                |          |                      |                                |
| 170 |                                | cluster_1_144_t                | text                           |          |                      |                                |
| 171 |                                | cluster_1_145_t                | text                           |          |                      |                                |
| 172 |                                | cluster_1_146_t                | text                           |          |                      |                                |
| 173 |                                | cluster_1_147_t                | text                           |          |                      |                                |
| 174 |                                | cluster_1_148_n                | numeric(19, 10)                |          |                      |                                |
| 175 |                                | cluster_1_149_d                | timestamp(6) without time zone |          |                      |                                |
| 176 |                                | cluster_1_150_n                | numeric(19, 10)                |          |                      |                                |
| 177 |                                | cluster_1_151_t                | text                           |          |                      |                                |
| 178 |                                | cluster_1_154_d                | timestamp(6) without time zone |          |                      |                                |
| 179 |                                | cluster_1_155_t                | text                           |          |                      |                                |
| 180 |                                | cluster_1_156_t                | text                           |          |                      |                                |
| 181 |                                | cluster_1_157_t                | text                           |          |                      |                                |
| 182 |                                | cluster_1_159_d                | timestamp(6) without time zone |          |                      |                                |
| 183 |                                | cluster_1_160_t                | text                           |          |                      |                                |
| 184 |                                | cluster_1_161_d                | timestamp(6) without time zone |          |                      |                                |
| 185 |                                | cluster_1_162_t                | text                           |          |                      |                                |
| 186 |                                | cluster_1_163_d                | timestamp(6) without time zone |          |                      |                                |
| 187 |                                | cluster_1_164_t                | text                           |          |                      |                                |
| 188 |                                | cluster_1_165_t                | text                           |          |                      |                                |
| 189 |                                | cluster_1_166_t                | text                           |          |                      |                                |
| 190 |                                | cluster_1_167_t                | text                           |          |                      |                                |
| 191 |                                | cluster_1_168_t                | text                           |          |                      |                                |



## ソース
```
CREATE OR REPLACE VIEW public.view_report_334 AS 
 SELECT rep_top_id,
    rep_top_name,
    public_status,
    edit_refer_status,
    rep_top_org,
    rev_no,
    def_top_id,
    report_type,
    rep_sheet_count,
    display_sheet_number,
    server_version,
    top_remarks1,
    top_remarks2,
    top_remarks3,
    top_remarks4,
    top_remarks5,
    top_remarks6,
    top_remarks7,
    top_remarks8,
    top_remarks9,
    top_remarks10,
    sys_regist_term,
    sys_regist_user,
    sys_regist_time,
    sys_update_term,
    sys_update_user,
    sys_update_time,
    cluster_1_0_t,
    cluster_1_1_t,
    cluster_1_2_t,
    cluster_1_3_t,
    cluster_1_4_t,
    cluster_1_5_t,
    cluster_1_6_t,
    cluster_1_7_t,
    cluster_1_8_t,
    cluster_1_9_t,
    cluster_1_10_t,
    cluster_1_11_t,
    cluster_1_12_t,
    cluster_1_13_t,
    cluster_1_14_t,
    cluster_1_15_t,
    cluster_1_16_t,
    cluster_1_17_t,
    cluster_1_18_t,
    cluster_1_19_t,
    cluster_1_20_t,
    cluster_1_21_n,
    cluster_1_22_t,
    cluster_1_23_t,
    cluster_1_24_t,
    cluster_1_25_t,
    cluster_1_26_n,
    cluster_1_27_t,
    cluster_1_28_t,
    cluster_1_29_t,
    cluster_1_30_t,
    cluster_1_31_n,
    cluster_1_32_t,
    cluster_1_33_t,
    cluster_1_34_t,
    cluster_1_35_t,
    cluster_1_36_t,
    cluster_1_37_n,
    cluster_1_38_t,
    cluster_1_39_t,
    cluster_1_40_t,
    cluster_1_41_t,
    cluster_1_42_t,
    cluster_1_43_n,
    cluster_1_44_t,
    cluster_1_45_t,
    cluster_1_46_t,
    cluster_1_47_t,
    cluster_1_48_t,
    cluster_1_49_n,
    cluster_1_50_t,
    cluster_1_51_t,
    cluster_1_52_t,
    cluster_1_53_t,
    cluster_1_54_t,
    cluster_1_55_n,
    cluster_1_56_t,
    cluster_1_57_t,
    cluster_1_58_t,
    cluster_1_59_t,
    cluster_1_60_n,
    cluster_1_61_t,
    cluster_1_62_t,
    cluster_1_63_t,
    cluster_1_64_t,
    cluster_1_65_n,
    cluster_1_66_t,
    cluster_1_67_t,
    cluster_1_69_t,
    cluster_1_70_n,
    cluster_1_71_t,
    cluster_1_72_t,
    cluster_1_74_t,
    cluster_1_75_n,
    cluster_1_76_t,
    cluster_1_77_t,
    cluster_1_78_t,
    cluster_1_79_t,
    cluster_1_80_t,
    cluster_1_81_n,
    cluster_1_82_t,
    cluster_1_83_t,
    cluster_1_84_t,
    cluster_1_85_t,
    cluster_1_86_t,
    cluster_1_87_n,
    cluster_1_88_t,
    cluster_1_89_t,
    cluster_1_90_t,
    cluster_1_91_t,
    cluster_1_92_n,
    cluster_1_93_t,
    cluster_1_94_t,
    cluster_1_95_t,
    cluster_1_96_t,
    cluster_1_97_n,
    cluster_1_98_t,
    cluster_1_99_t,
    cluster_1_100_t,
    cluster_1_101_t,
    cluster_1_102_n,
    cluster_1_103_t,
    cluster_1_104_t,
    cluster_1_105_t,
    cluster_1_106_t,
    cluster_1_107_n,
    cluster_1_108_t,
    cluster_1_109_t,
    cluster_1_110_t,
    cluster_1_111_t,
    cluster_1_112_t,
    cluster_1_113_n,
    cluster_1_114_t,
    cluster_1_115_t,
    cluster_1_116_t,
    cluster_1_117_t,
    cluster_1_118_n,
    cluster_1_119_t,
    cluster_1_120_t,
    cluster_1_121_t,
    cluster_1_122_t,
    cluster_1_123_n,
    cluster_1_124_t,
    cluster_1_125_t,
    cluster_1_126_t,
    cluster_1_127_t,
    cluster_1_128_t,
    cluster_1_129_n,
    cluster_1_130_t,
    cluster_1_131_t,
    cluster_1_132_n,
    cluster_1_133_n,
    cluster_1_134_n,
    cluster_1_135_n,
    cluster_1_136_n,
    cluster_1_137_t,
    cluster_1_138_t,
    cluster_1_139_n,
    cluster_1_140_n,
    cluster_1_141_n,
    cluster_1_142_n,
    cluster_1_143_n,
    cluster_1_144_t,
    cluster_1_145_t,
    cluster_1_146_t,
    cluster_1_147_t,
    cluster_1_148_n,
    cluster_1_149_d,
    cluster_1_150_n,
    cluster_1_151_t,
    cluster_1_154_d,
    cluster_1_155_t,
    cluster_1_156_t,
    cluster_1_157_t,
    cluster_1_159_d,
    cluster_1_160_t,
    cluster_1_161_d,
    cluster_1_162_t,
    cluster_1_163_d,
    cluster_1_164_t,
    cluster_1_165_t,
    cluster_1_166_t,
    cluster_1_167_t,
    cluster_1_168_t
   FROM ( SELECT report_384.rep_top_id,
            report_384.rep_top_name,
            report_384.public_status,
            report_384.edit_refer_status,
            report_384.rep_top_org,
            report_384.rev_no,
            report_384.def_top_id,
            report_384.report_type,
            report_384.rep_sheet_count,
            report_384.display_sheet_number,
            report_384.server_version,
            report_384.top_remarks1,
            report_384.top_remarks2,
            report_384.top_remarks3,
            report_384.top_remarks4,
            report_384.top_remarks5,
            report_384.top_remarks6,
            report_384.top_remarks7,
            report_384.top_remarks8,
            report_384.top_remarks9,
            report_384.top_remarks10,
            report_384.sys_regist_term,
            report_384.sys_regist_user,
            report_384.sys_regist_time,
            report_384.sys_update_term,
            report_384.sys_update_user,
            report_384.sys_update_time,
            report_384.cluster_1_0_t,
            report_384.cluster_1_1_t,
            report_384.cluster_1_2_t,
            report_384.cluster_1_3_t,
            report_384.cluster_1_4_t,
            report_384.cluster_1_5_t,
            report_384.cluster_1_6_t,
            report_384.cluster_1_7_t,
            report_384.cluster_1_8_t,
            report_384.cluster_1_9_t,
            report_384.cluster_1_10_t,
            report_384.cluster_1_11_t,
            report_384.cluster_1_12_t,
            report_384.cluster_1_13_t,
            report_384.cluster_1_14_t,
            report_384.cluster_1_15_t,
            report_384.cluster_1_16_t,
            report_384.cluster_1_17_t,
            report_384.cluster_1_18_t,
            report_384.cluster_1_19_t,
            report_384.cluster_1_20_t,
            report_384.cluster_1_21_n,
            report_384.cluster_1_22_t,
            report_384.cluster_1_23_t,
            report_384.cluster_1_24_t,
            report_384.cluster_1_25_t,
            report_384.cluster_1_26_n,
            report_384.cluster_1_27_t,
            report_384.cluster_1_28_t,
            report_384.cluster_1_29_t,
            report_384.cluster_1_30_t,
            report_384.cluster_1_31_n,
            report_384.cluster_1_32_t,
            report_384.cluster_1_33_t,
            report_384.cluster_1_34_t,
            report_384.cluster_1_35_t,
            report_384.cluster_1_36_t,
            report_384.cluster_1_37_n,
            report_384.cluster_1_38_t,
            report_384.cluster_1_39_t,
            report_384.cluster_1_40_t,
            report_384.cluster_1_41_t,
            report_384.cluster_1_42_t,
            report_384.cluster_1_43_n,
            report_384.cluster_1_44_t,
            report_384.cluster_1_45_t,
            report_384.cluster_1_46_t,
            report_384.cluster_1_47_t,
            report_384.cluster_1_48_t,
            report_384.cluster_1_49_n,
            report_384.cluster_1_50_t,
            report_384.cluster_1_51_t,
            report_384.cluster_1_52_t,
            report_384.cluster_1_53_t,
            report_384.cluster_1_54_t,
            report_384.cluster_1_55_n,
            report_384.cluster_1_56_t,
            report_384.cluster_1_57_t,
            report_384.cluster_1_58_t,
            report_384.cluster_1_59_t,
            report_384.cluster_1_60_n,
            report_384.cluster_1_61_t,
            report_384.cluster_1_62_t,
            report_384.cluster_1_63_t,
            report_384.cluster_1_64_t,
            report_384.cluster_1_65_n,
            report_384.cluster_1_66_t,
            report_384.cluster_1_67_t,
            report_384.cluster_1_69_t,
            report_384.cluster_1_70_n,
            report_384.cluster_1_71_t,
            report_384.cluster_1_72_t,
            report_384.cluster_1_74_t,
            report_384.cluster_1_75_n,
            report_384.cluster_1_76_t,
            report_384.cluster_1_77_t,
            report_384.cluster_1_78_t,
            report_384.cluster_1_79_t,
            report_384.cluster_1_80_t,
            report_384.cluster_1_81_n,
            report_384.cluster_1_82_t,
            report_384.cluster_1_83_t,
            report_384.cluster_1_84_t,
            report_384.cluster_1_85_t,
            report_384.cluster_1_86_t,
            report_384.cluster_1_87_n,
            report_384.cluster_1_88_t,
            report_384.cluster_1_89_t,
            report_384.cluster_1_90_t,
            report_384.cluster_1_91_t,
            report_384.cluster_1_92_n,
            report_384.cluster_1_93_t,
            report_384.cluster_1_94_t,
            report_384.cluster_1_95_t,
            report_384.cluster_1_96_t,
            report_384.cluster_1_97_n,
            report_384.cluster_1_98_t,
            report_384.cluster_1_99_t,
            report_384.cluster_1_100_t,
            report_384.cluster_1_101_t,
            report_384.cluster_1_102_n,
            report_384.cluster_1_103_t,
            report_384.cluster_1_104_t,
            report_384.cluster_1_105_t,
            report_384.cluster_1_106_t,
            report_384.cluster_1_107_n,
            report_384.cluster_1_108_t,
            report_384.cluster_1_109_t,
            report_384.cluster_1_110_t,
            report_384.cluster_1_111_t,
            report_384.cluster_1_112_t,
            report_384.cluster_1_113_n,
            report_384.cluster_1_114_t,
            report_384.cluster_1_115_t,
            report_384.cluster_1_116_t,
            report_384.cluster_1_117_t,
            report_384.cluster_1_118_n,
            report_384.cluster_1_119_t,
            report_384.cluster_1_120_t,
            report_384.cluster_1_121_t,
            report_384.cluster_1_122_t,
            report_384.cluster_1_123_n,
            report_384.cluster_1_124_t,
            report_384.cluster_1_125_t,
            report_384.cluster_1_126_t,
            report_384.cluster_1_127_t,
            report_384.cluster_1_128_t,
            report_384.cluster_1_129_n,
            report_384.cluster_1_130_t,
            report_384.cluster_1_131_t,
            report_384.cluster_1_132_n,
            report_384.cluster_1_133_n,
            report_384.cluster_1_134_n,
            report_384.cluster_1_135_n,
            report_384.cluster_1_136_n,
            report_384.cluster_1_137_t,
            report_384.cluster_1_138_t,
            report_384.cluster_1_139_n,
            report_384.cluster_1_140_n,
            report_384.cluster_1_141_n,
            report_384.cluster_1_142_n,
            report_384.cluster_1_143_n,
            report_384.cluster_1_144_t,
            report_384.cluster_1_145_t,
            report_384.cluster_1_146_t,
            report_384.cluster_1_147_t,
            report_384.cluster_1_148_n,
            report_384.cluster_1_149_d,
            report_384.cluster_1_150_n,
            report_384.cluster_1_151_t,
            report_384.cluster_1_154_d,
            report_384.cluster_1_155_t,
            report_384.cluster_1_156_t,
            report_384.cluster_1_157_t,
            report_384.cluster_1_159_d,
            report_384.cluster_1_160_t,
            report_384.cluster_1_161_d,
            report_384.cluster_1_162_t,
            report_384.cluster_1_163_d,
            report_384.cluster_1_164_t,
            report_384.cluster_1_165_t,
            report_384.cluster_1_166_t,
            report_384.cluster_1_167_t,
            report_384.cluster_1_168_t
           FROM report_384
          WHERE ((report_384.rep_top_id IN ( SELECT rep_top.rep_top_id
                   FROM rep_top
                  WHERE (rep_top.deleted = (0)::numeric))) AND (report_384.rep_top_id IN ( SELECT rep_current.rep_top_id
                   FROM rep_current)))
        UNION ALL
         SELECT report_390.rep_top_id,
            report_390.rep_top_name,
            report_390.public_status,
            report_390.edit_refer_status,
            report_390.rep_top_org,
            report_390.rev_no,
            report_390.def_top_id,
            report_390.report_type,
            report_390.rep_sheet_count,
            report_390.display_sheet_number,
            report_390.server_version,
            report_390.top_remarks1,
            report_390.top_remarks2,
            report_390.top_remarks3,
            report_390.top_remarks4,
            report_390.top_remarks5,
            report_390.top_remarks6,
            report_390.top_remarks7,
            report_390.top_remarks8,
            report_390.top_remarks9,
            report_390.top_remarks10,
            report_390.sys_regist_term,
            report_390.sys_regist_user,
            report_390.sys_regist_time,
            report_390.sys_update_term,
            report_390.sys_update_user,
            report_390.sys_update_time,
            report_390.cluster_1_0_t,
            report_390.cluster_1_1_t,
            report_390.cluster_1_2_t,
            report_390.cluster_1_3_t,
            report_390.cluster_1_4_t,
            report_390.cluster_1_5_t,
            report_390.cluster_1_6_t,
            report_390.cluster_1_7_t,
            report_390.cluster_1_8_t,
            report_390.cluster_1_9_t,
            report_390.cluster_1_10_t,
            report_390.cluster_1_11_t,
            report_390.cluster_1_12_t,
            report_390.cluster_1_13_t,
            report_390.cluster_1_14_t,
            report_390.cluster_1_15_t,
            report_390.cluster_1_16_t,
            report_390.cluster_1_17_t,
            report_390.cluster_1_18_t,
            report_390.cluster_1_19_t,
            report_390.cluster_1_20_t,
            report_390.cluster_1_21_n,
            report_390.cluster_1_22_t,
            report_390.cluster_1_23_t,
            report_390.cluster_1_24_t,
            report_390.cluster_1_25_t,
            report_390.cluster_1_26_n,
            report_390.cluster_1_27_t,
            report_390.cluster_1_28_t,
            report_390.cluster_1_29_t,
            report_390.cluster_1_30_t,
            report_390.cluster_1_31_n,
            report_390.cluster_1_32_t,
            report_390.cluster_1_33_t,
            report_390.cluster_1_34_t,
            report_390.cluster_1_35_t,
            report_390.cluster_1_36_t,
            report_390.cluster_1_37_n,
            report_390.cluster_1_38_t,
            report_390.cluster_1_39_t,
            report_390.cluster_1_40_t,
            report_390.cluster_1_41_t,
            report_390.cluster_1_42_t,
            report_390.cluster_1_43_n,
            report_390.cluster_1_44_t,
            report_390.cluster_1_45_t,
            report_390.cluster_1_46_t,
            report_390.cluster_1_47_t,
            report_390.cluster_1_48_t,
            report_390.cluster_1_49_n,
            report_390.cluster_1_50_t,
            report_390.cluster_1_51_t,
            report_390.cluster_1_52_t,
            report_390.cluster_1_53_t,
            report_390.cluster_1_54_t,
            report_390.cluster_1_55_n,
            report_390.cluster_1_56_t,
            report_390.cluster_1_57_t,
            report_390.cluster_1_58_t,
            report_390.cluster_1_59_t,
            report_390.cluster_1_60_n,
            report_390.cluster_1_61_t,
            report_390.cluster_1_62_t,
            report_390.cluster_1_63_t,
            report_390.cluster_1_64_t,
            report_390.cluster_1_65_n,
            report_390.cluster_1_66_t,
            report_390.cluster_1_67_t,
            report_390.cluster_1_69_t,
            report_390.cluster_1_70_n,
            report_390.cluster_1_71_t,
            report_390.cluster_1_72_t,
            report_390.cluster_1_74_t,
            report_390.cluster_1_75_n,
            report_390.cluster_1_76_t,
            report_390.cluster_1_77_t,
            report_390.cluster_1_78_t,
            report_390.cluster_1_79_t,
            report_390.cluster_1_80_t,
            report_390.cluster_1_81_n,
            report_390.cluster_1_82_t,
            report_390.cluster_1_83_t,
            report_390.cluster_1_84_t,
            report_390.cluster_1_85_t,
            report_390.cluster_1_86_t,
            report_390.cluster_1_87_n,
            report_390.cluster_1_88_t,
            report_390.cluster_1_89_t,
            report_390.cluster_1_90_t,
            report_390.cluster_1_91_t,
            report_390.cluster_1_92_n,
            report_390.cluster_1_93_t,
            report_390.cluster_1_94_t,
            report_390.cluster_1_95_t,
            report_390.cluster_1_96_t,
            report_390.cluster_1_97_n,
            report_390.cluster_1_98_t,
            report_390.cluster_1_99_t,
            report_390.cluster_1_100_t,
            report_390.cluster_1_101_t,
            report_390.cluster_1_102_n,
            report_390.cluster_1_103_t,
            report_390.cluster_1_104_t,
            report_390.cluster_1_105_t,
            report_390.cluster_1_106_t,
            report_390.cluster_1_107_n,
            report_390.cluster_1_108_t,
            report_390.cluster_1_109_t,
            report_390.cluster_1_110_t,
            report_390.cluster_1_111_t,
            report_390.cluster_1_112_t,
            report_390.cluster_1_113_n,
            report_390.cluster_1_114_t,
            report_390.cluster_1_115_t,
            report_390.cluster_1_116_t,
            report_390.cluster_1_117_t,
            report_390.cluster_1_118_n,
            report_390.cluster_1_119_t,
            report_390.cluster_1_120_t,
            report_390.cluster_1_121_t,
            report_390.cluster_1_122_t,
            report_390.cluster_1_123_n,
            report_390.cluster_1_124_t,
            report_390.cluster_1_125_t,
            report_390.cluster_1_126_t,
            report_390.cluster_1_127_t,
            report_390.cluster_1_128_t,
            report_390.cluster_1_129_n,
            report_390.cluster_1_130_t,
            report_390.cluster_1_131_t,
            report_390.cluster_1_132_n,
            report_390.cluster_1_133_n,
            report_390.cluster_1_134_n,
            report_390.cluster_1_135_n,
            report_390.cluster_1_136_n,
            report_390.cluster_1_137_t,
            report_390.cluster_1_138_t,
            report_390.cluster_1_139_n,
            report_390.cluster_1_140_n,
            report_390.cluster_1_141_n,
            report_390.cluster_1_142_n,
            report_390.cluster_1_143_n,
            report_390.cluster_1_144_t,
            report_390.cluster_1_145_t,
            report_390.cluster_1_146_t,
            report_390.cluster_1_147_t,
            report_390.cluster_1_148_n,
            report_390.cluster_1_149_d,
            report_390.cluster_1_150_n,
            report_390.cluster_1_151_t,
            report_390.cluster_1_154_d,
            report_390.cluster_1_155_t,
            report_390.cluster_1_156_t,
            report_390.cluster_1_157_t,
            report_390.cluster_1_159_d,
            report_390.cluster_1_160_t,
            report_390.cluster_1_161_d,
            report_390.cluster_1_162_t,
            report_390.cluster_1_163_d,
            report_390.cluster_1_164_t,
            report_390.cluster_1_165_t,
            report_390.cluster_1_166_t,
            report_390.cluster_1_167_t,
            report_390.cluster_1_168_t
           FROM report_390
          WHERE ((report_390.rep_top_id IN ( SELECT rep_top.rep_top_id
                   FROM rep_top
                  WHERE (rep_top.deleted = (0)::numeric))) AND (report_390.rep_top_id IN ( SELECT rep_current.rep_top_id
                   FROM rep_current)))) reporttable;

```



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | schemaname                     | public                                                                                               |
|   2 | viewname                       | view_report_334                                                                                      |
|   3 | viewowner                      | postgres                                                                                             |
|   4 | definition                     |  SELECT rep_top_id,<br>    rep_top_name,<br>    public_status,<br>    edit_refer_status,<br>    rep_top_org,<br>    rev_no,<br>    def_top_id,<br>    report_type,<br>    rep_sheet_count,<br>    display_sheet_number,<br>    server_version,<br>    top_remarks1,<br>    top_remarks2,<br>    top_remarks3,<br>    top_remarks4,<br>    top_remarks5,<br>    top_remarks6,<br>    top_remarks7,<br>    top_remarks8,<br>    top_remarks9,<br>    top_remarks10,<br>    sys_regist_term,<br>    sys_regist_user,<br>    sys_regist_time,<br>    sys_update_term,<br>    sys_update_user,<br>    sys_update_time,<br>    cluster_1_0_t,<br>    cluster_1_1_t,<br>    cluster_1_2_t,<br>    cluster_1_3_t,<br>    cluster_1_4_t,<br>    cluster_1_5_t,<br>    cluster_1_6_t,<br>    cluster_1_7_t,<br>    cluster_1_8_t,<br>    cluster_1_9_t,<br>    cluster_1_10_t,<br>    cluster_1_11_t,<br>    cluster_1_12_t,<br>    cluster_1_13_t,<br>    cluster_1_14_t,<br>    cluster_1_15_t,<br>    cluster_1_16_t,<br>    cluster_1_17_t,<br>    cluster_1_18_t,<br>    cluster_1_19_t,<br>    cluster_1_20_t,<br>    cluster_1_21_n,<br>    cluster_1_22_t,<br>    cluster_1_23_t,<br>    cluster_1_24_t,<br>    cluster_1_25_t,<br>    cluster_1_26_n,<br>    cluster_1_27_t,<br>    cluster_1_28_t,<br>    cluster_1_29_t,<br>    cluster_1_30_t,<br>    cluster_1_31_n,<br>    cluster_1_32_t,<br>    cluster_1_33_t,<br>    cluster_1_34_t,<br>    cluster_1_35_t,<br>    cluster_1_36_t,<br>    cluster_1_37_n,<br>    cluster_1_38_t,<br>    cluster_1_39_t,<br>    cluster_1_40_t,<br>    cluster_1_41_t,<br>    cluster_1_42_t,<br>    cluster_1_43_n,<br>    cluster_1_44_t,<br>    cluster_1_45_t,<br>    cluster_1_46_t,<br>    cluster_1_47_t,<br>    cluster_1_48_t,<br>    cluster_1_49_n,<br>    cluster_1_50_t,<br>    cluster_1_51_t,<br>    cluster_1_52_t,<br>    cluster_1_53_t,<br>    cluster_1_54_t,<br>    cluster_1_55_n,<br>    cluster_1_56_t,<br>    cluster_1_57_t,<br>    cluster_1_58_t,<br>    cluster_1_59_t,<br>    cluster_1_60_n,<br>    cluster_1_61_t,<br>    cluster_1_62_t,<br>    cluster_1_63_t,<br>    cluster_1_64_t,<br>    cluster_1_65_n,<br>    cluster_1_66_t,<br>    cluster_1_67_t,<br>    cluster_1_69_t,<br>    cluster_1_70_n,<br>    cluster_1_71_t,<br>    cluster_1_72_t,<br>    cluster_1_74_t,<br>    cluster_1_75_n,<br>    cluster_1_76_t,<br>    cluster_1_77_t,<br>    cluster_1_78_t,<br>    cluster_1_79_t,<br>    cluster_1_80_t,<br>    cluster_1_81_n,<br>    cluster_1_82_t,<br>    cluster_1_83_t,<br>    cluster_1_84_t,<br>    cluster_1_85_t,<br>    cluster_1_86_t,<br>    cluster_1_87_n,<br>    cluster_1_88_t,<br>    cluster_1_89_t,<br>    cluster_1_90_t,<br>    cluster_1_91_t,<br>    cluster_1_92_n,<br>    cluster_1_93_t,<br>    cluster_1_94_t,<br>    cluster_1_95_t,<br>    cluster_1_96_t,<br>    cluster_1_97_n,<br>    cluster_1_98_t,<br>    cluster_1_99_t,<br>    cluster_1_100_t,<br>    cluster_1_101_t,<br>    cluster_1_102_n,<br>    cluster_1_103_t,<br>    cluster_1_104_t,<br>    cluster_1_105_t,<br>    cluster_1_106_t,<br>    cluster_1_107_n,<br>    cluster_1_108_t,<br>    cluster_1_109_t,<br>    cluster_1_110_t,<br>    cluster_1_111_t,<br>    cluster_1_112_t,<br>    cluster_1_113_n,<br>    cluster_1_114_t,<br>    cluster_1_115_t,<br>    cluster_1_116_t,<br>    cluster_1_117_t,<br>    cluster_1_118_n,<br>    cluster_1_119_t,<br>    cluster_1_120_t,<br>    cluster_1_121_t,<br>    cluster_1_122_t,<br>    cluster_1_123_n,<br>    cluster_1_124_t,<br>    cluster_1_125_t,<br>    cluster_1_126_t,<br>    cluster_1_127_t,<br>    cluster_1_128_t,<br>    cluster_1_129_n,<br>    cluster_1_130_t,<br>    cluster_1_131_t,<br>    cluster_1_132_n,<br>    cluster_1_133_n,<br>    cluster_1_134_n,<br>    cluster_1_135_n,<br>    cluster_1_136_n,<br>    cluster_1_137_t,<br>    cluster_1_138_t,<br>    cluster_1_139_n,<br>    cluster_1_140_n,<br>    cluster_1_141_n,<br>    cluster_1_142_n,<br>    cluster_1_143_n,<br>    cluster_1_144_t,<br>    cluster_1_145_t,<br>    cluster_1_146_t,<br>    cluster_1_147_t,<br>    cluster_1_148_n,<br>    cluster_1_149_d,<br>    cluster_1_150_n,<br>    cluster_1_151_t,<br>    cluster_1_154_d,<br>    cluster_1_155_t,<br>    cluster_1_156_t,<br>    cluster_1_157_t,<br>    cluster_1_159_d,<br>    cluster_1_160_t,<br>    cluster_1_161_d,<br>    cluster_1_162_t,<br>    cluster_1_163_d,<br>    cluster_1_164_t,<br>    cluster_1_165_t,<br>    cluster_1_166_t,<br>    cluster_1_167_t,<br>    cluster_1_168_t<br>   FROM ( SELECT report_384.rep_top_id,<br>            report_384.rep_top_name,<br>            report_384.public_status,<br>            report_384.edit_refer_status,<br>            report_384.rep_top_org,<br>            report_384.rev_no,<br>            report_384.def_top_id,<br>            report_384.report_type,<br>            report_384.rep_sheet_count,<br>            report_384.display_sheet_number,<br>            report_384.server_version,<br>            report_384.top_remarks1,<br>            report_384.top_remarks2,<br>            report_384.top_remarks3,<br>            report_384.top_remarks4,<br>            report_384.top_remarks5,<br>            report_384.top_remarks6,<br>            report_384.top_remarks7,<br>            report_384.top_remarks8,<br>            report_384.top_remarks9,<br>            report_384.top_remarks10,<br>            report_384.sys_regist_term,<br>            report_384.sys_regist_user,<br>            report_384.sys_regist_time,<br>            report_384.sys_update_term,<br>            report_384.sys_update_user,<br>            report_384.sys_update_time,<br>            report_384.cluster_1_0_t,<br>            report_384.cluster_1_1_t,<br>            report_384.cluster_1_2_t,<br>            report_384.cluster_1_3_t,<br>            report_384.cluster_1_4_t,<br>            report_384.cluster_1_5_t,<br>            report_384.cluster_1_6_t,<br>            report_384.cluster_1_7_t,<br>            report_384.cluster_1_8_t,<br>            report_384.cluster_1_9_t,<br>            report_384.cluster_1_10_t,<br>            report_384.cluster_1_11_t,<br>            report_384.cluster_1_12_t,<br>            report_384.cluster_1_13_t,<br>            report_384.cluster_1_14_t,<br>            report_384.cluster_1_15_t,<br>            report_384.cluster_1_16_t,<br>            report_384.cluster_1_17_t,<br>            report_384.cluster_1_18_t,<br>            report_384.cluster_1_19_t,<br>            report_384.cluster_1_20_t,<br>            report_384.cluster_1_21_n,<br>            report_384.cluster_1_22_t,<br>            report_384.cluster_1_23_t,<br>            report_384.cluster_1_24_t,<br>            report_384.cluster_1_25_t,<br>            report_384.cluster_1_26_n,<br>            report_384.cluster_1_27_t,<br>            report_384.cluster_1_28_t,<br>            report_384.cluster_1_29_t,<br>            report_384.cluster_1_30_t,<br>            report_384.cluster_1_31_n,<br>            report_384.cluster_1_32_t,<br>            report_384.cluster_1_33_t,<br>            report_384.cluster_1_34_t,<br>            report_384.cluster_1_35_t,<br>            report_384.cluster_1_36_t,<br>            report_384.cluster_1_37_n,<br>            report_384.cluster_1_38_t,<br>            report_384.cluster_1_39_t,<br>            report_384.cluster_1_40_t,<br>            report_384.cluster_1_41_t,<br>            report_384.cluster_1_42_t,<br>            report_384.cluster_1_43_n,<br>            report_384.cluster_1_44_t,<br>            report_384.cluster_1_45_t,<br>            report_384.cluster_1_46_t,<br>            report_384.cluster_1_47_t,<br>            report_384.cluster_1_48_t,<br>            report_384.cluster_1_49_n,<br>            report_384.cluster_1_50_t,<br>            report_384.cluster_1_51_t,<br>            report_384.cluster_1_52_t,<br>            report_384.cluster_1_53_t,<br>            report_384.cluster_1_54_t,<br>            report_384.cluster_1_55_n,<br>            report_384.cluster_1_56_t,<br>            report_384.cluster_1_57_t,<br>            report_384.cluster_1_58_t,<br>            report_384.cluster_1_59_t,<br>            report_384.cluster_1_60_n,<br>            report_384.cluster_1_61_t,<br>            report_384.cluster_1_62_t,<br>            report_384.cluster_1_63_t,<br>            report_384.cluster_1_64_t,<br>            report_384.cluster_1_65_n,<br>            report_384.cluster_1_66_t,<br>            report_384.cluster_1_67_t,<br>            report_384.cluster_1_69_t,<br>            report_384.cluster_1_70_n,<br>            report_384.cluster_1_71_t,<br>            report_384.cluster_1_72_t,<br>            report_384.cluster_1_74_t,<br>            report_384.cluster_1_75_n,<br>            report_384.cluster_1_76_t,<br>            report_384.cluster_1_77_t,<br>            report_384.cluster_1_78_t,<br>            report_384.cluster_1_79_t,<br>            report_384.cluster_1_80_t,<br>            report_384.cluster_1_81_n,<br>            report_384.cluster_1_82_t,<br>            report_384.cluster_1_83_t,<br>            report_384.cluster_1_84_t,<br>            report_384.cluster_1_85_t,<br>            report_384.cluster_1_86_t,<br>            report_384.cluster_1_87_n,<br>            report_384.cluster_1_88_t,<br>            report_384.cluster_1_89_t,<br>            report_384.cluster_1_90_t,<br>            report_384.cluster_1_91_t,<br>            report_384.cluster_1_92_n,<br>            report_384.cluster_1_93_t,<br>            report_384.cluster_1_94_t,<br>            report_384.cluster_1_95_t,<br>            report_384.cluster_1_96_t,<br>            report_384.cluster_1_97_n,<br>            report_384.cluster_1_98_t,<br>            report_384.cluster_1_99_t,<br>            report_384.cluster_1_100_t,<br>            report_384.cluster_1_101_t,<br>            report_384.cluster_1_102_n,<br>            report_384.cluster_1_103_t,<br>            report_384.cluster_1_104_t,<br>            report_384.cluster_1_105_t,<br>            report_384.cluster_1_106_t,<br>            report_384.cluster_1_107_n,<br>            report_384.cluster_1_108_t,<br>            report_384.cluster_1_109_t,<br>            report_384.cluster_1_110_t,<br>            report_384.cluster_1_111_t,<br>            report_384.cluster_1_112_t,<br>            report_384.cluster_1_113_n,<br>            report_384.cluster_1_114_t,<br>            report_384.cluster_1_115_t,<br>            report_384.cluster_1_116_t,<br>            report_384.cluster_1_117_t,<br>            report_384.cluster_1_118_n,<br>            report_384.cluster_1_119_t,<br>            report_384.cluster_1_120_t,<br>            report_384.cluster_1_121_t,<br>            report_384.cluster_1_122_t,<br>            report_384.cluster_1_123_n,<br>            report_384.cluster_1_124_t,<br>            report_384.cluster_1_125_t,<br>            report_384.cluster_1_126_t,<br>            report_384.cluster_1_127_t,<br>            report_384.cluster_1_128_t,<br>            report_384.cluster_1_129_n,<br>            report_384.cluster_1_130_t,<br>            report_384.cluster_1_131_t,<br>            report_384.cluster_1_132_n,<br>            report_384.cluster_1_133_n,<br>            report_384.cluster_1_134_n,<br>            report_384.cluster_1_135_n,<br>            report_384.cluster_1_136_n,<br>            report_384.cluster_1_137_t,<br>            report_384.cluster_1_138_t,<br>            report_384.cluster_1_139_n,<br>            report_384.cluster_1_140_n,<br>            report_384.cluster_1_141_n,<br>            report_384.cluster_1_142_n,<br>            report_384.cluster_1_143_n,<br>            report_384.cluster_1_144_t,<br>            report_384.cluster_1_145_t,<br>            report_384.cluster_1_146_t,<br>            report_384.cluster_1_147_t,<br>            report_384.cluster_1_148_n,<br>            report_384.cluster_1_149_d,<br>            report_384.cluster_1_150_n,<br>            report_384.cluster_1_151_t,<br>            report_384.cluster_1_154_d,<br>            report_384.cluster_1_155_t,<br>            report_384.cluster_1_156_t,<br>            report_384.cluster_1_157_t,<br>            report_384.cluster_1_159_d,<br>            report_384.cluster_1_160_t,<br>            report_384.cluster_1_161_d,<br>            report_384.cluster_1_162_t,<br>            report_384.cluster_1_163_d,<br>            report_384.cluster_1_164_t,<br>            report_384.cluster_1_165_t,<br>            report_384.cluster_1_166_t,<br>            report_384.cluster_1_167_t,<br>            report_384.cluster_1_168_t<br>           FROM report_384<br>          WHERE ((report_384.rep_top_id IN ( SELECT rep_top.rep_top_id<br>                   FROM rep_top<br>                  WHERE (rep_top.deleted = (0)::numeric))) AND (report_384.rep_top_id IN ( SELECT rep_current.rep_top_id<br>                   FROM rep_current)))<br>        UNION ALL<br>         SELECT report_390.rep_top_id,<br>            report_390.rep_top_name,<br>            report_390.public_status,<br>            report_390.edit_refer_status,<br>            report_390.rep_top_org,<br>            report_390.rev_no,<br>            report_390.def_top_id,<br>            report_390.report_type,<br>            report_390.rep_sheet_count,<br>            report_390.display_sheet_number,<br>            report_390.server_version,<br>            report_390.top_remarks1,<br>            report_390.top_remarks2,<br>            report_390.top_remarks3,<br>            report_390.top_remarks4,<br>            report_390.top_remarks5,<br>            report_390.top_remarks6,<br>            report_390.top_remarks7,<br>            report_390.top_remarks8,<br>            report_390.top_remarks9,<br>            report_390.top_remarks10,<br>            report_390.sys_regist_term,<br>            report_390.sys_regist_user,<br>            report_390.sys_regist_time,<br>            report_390.sys_update_term,<br>            report_390.sys_update_user,<br>            report_390.sys_update_time,<br>            report_390.cluster_1_0_t,<br>            report_390.cluster_1_1_t,<br>            report_390.cluster_1_2_t,<br>            report_390.cluster_1_3_t,<br>            report_390.cluster_1_4_t,<br>            report_390.cluster_1_5_t,<br>            report_390.cluster_1_6_t,<br>            report_390.cluster_1_7_t,<br>            report_390.cluster_1_8_t,<br>            report_390.cluster_1_9_t,<br>            report_390.cluster_1_10_t,<br>            report_390.cluster_1_11_t,<br>            report_390.cluster_1_12_t,<br>            report_390.cluster_1_13_t,<br>            report_390.cluster_1_14_t,<br>            report_390.cluster_1_15_t,<br>            report_390.cluster_1_16_t,<br>            report_390.cluster_1_17_t,<br>            report_390.cluster_1_18_t,<br>            report_390.cluster_1_19_t,<br>            report_390.cluster_1_20_t,<br>            report_390.cluster_1_21_n,<br>            report_390.cluster_1_22_t,<br>            report_390.cluster_1_23_t,<br>            report_390.cluster_1_24_t,<br>            report_390.cluster_1_25_t,<br>            report_390.cluster_1_26_n,<br>            report_390.cluster_1_27_t,<br>            report_390.cluster_1_28_t,<br>            report_390.cluster_1_29_t,<br>            report_390.cluster_1_30_t,<br>            report_390.cluster_1_31_n,<br>            report_390.cluster_1_32_t,<br>            report_390.cluster_1_33_t,<br>            report_390.cluster_1_34_t,<br>            report_390.cluster_1_35_t,<br>            report_390.cluster_1_36_t,<br>            report_390.cluster_1_37_n,<br>            report_390.cluster_1_38_t,<br>            report_390.cluster_1_39_t,<br>            report_390.cluster_1_40_t,<br>            report_390.cluster_1_41_t,<br>            report_390.cluster_1_42_t,<br>            report_390.cluster_1_43_n,<br>            report_390.cluster_1_44_t,<br>            report_390.cluster_1_45_t,<br>            report_390.cluster_1_46_t,<br>            report_390.cluster_1_47_t,<br>            report_390.cluster_1_48_t,<br>            report_390.cluster_1_49_n,<br>            report_390.cluster_1_50_t,<br>            report_390.cluster_1_51_t,<br>            report_390.cluster_1_52_t,<br>            report_390.cluster_1_53_t,<br>            report_390.cluster_1_54_t,<br>            report_390.cluster_1_55_n,<br>            report_390.cluster_1_56_t,<br>            report_390.cluster_1_57_t,<br>            report_390.cluster_1_58_t,<br>            report_390.cluster_1_59_t,<br>            report_390.cluster_1_60_n,<br>            report_390.cluster_1_61_t,<br>            report_390.cluster_1_62_t,<br>            report_390.cluster_1_63_t,<br>            report_390.cluster_1_64_t,<br>            report_390.cluster_1_65_n,<br>            report_390.cluster_1_66_t,<br>            report_390.cluster_1_67_t,<br>            report_390.cluster_1_69_t,<br>            report_390.cluster_1_70_n,<br>            report_390.cluster_1_71_t,<br>            report_390.cluster_1_72_t,<br>            report_390.cluster_1_74_t,<br>            report_390.cluster_1_75_n,<br>            report_390.cluster_1_76_t,<br>            report_390.cluster_1_77_t,<br>            report_390.cluster_1_78_t,<br>            report_390.cluster_1_79_t,<br>            report_390.cluster_1_80_t,<br>            report_390.cluster_1_81_n,<br>            report_390.cluster_1_82_t,<br>            report_390.cluster_1_83_t,<br>            report_390.cluster_1_84_t,<br>            report_390.cluster_1_85_t,<br>            report_390.cluster_1_86_t,<br>            report_390.cluster_1_87_n,<br>            report_390.cluster_1_88_t,<br>            report_390.cluster_1_89_t,<br>            report_390.cluster_1_90_t,<br>            report_390.cluster_1_91_t,<br>            report_390.cluster_1_92_n,<br>            report_390.cluster_1_93_t,<br>            report_390.cluster_1_94_t,<br>            report_390.cluster_1_95_t,<br>            report_390.cluster_1_96_t,<br>            report_390.cluster_1_97_n,<br>            report_390.cluster_1_98_t,<br>            report_390.cluster_1_99_t,<br>            report_390.cluster_1_100_t,<br>            report_390.cluster_1_101_t,<br>            report_390.cluster_1_102_n,<br>            report_390.cluster_1_103_t,<br>            report_390.cluster_1_104_t,<br>            report_390.cluster_1_105_t,<br>            report_390.cluster_1_106_t,<br>            report_390.cluster_1_107_n,<br>            report_390.cluster_1_108_t,<br>            report_390.cluster_1_109_t,<br>            report_390.cluster_1_110_t,<br>            report_390.cluster_1_111_t,<br>            report_390.cluster_1_112_t,<br>            report_390.cluster_1_113_n,<br>            report_390.cluster_1_114_t,<br>            report_390.cluster_1_115_t,<br>            report_390.cluster_1_116_t,<br>            report_390.cluster_1_117_t,<br>            report_390.cluster_1_118_n,<br>            report_390.cluster_1_119_t,<br>            report_390.cluster_1_120_t,<br>            report_390.cluster_1_121_t,<br>            report_390.cluster_1_122_t,<br>            report_390.cluster_1_123_n,<br>            report_390.cluster_1_124_t,<br>            report_390.cluster_1_125_t,<br>            report_390.cluster_1_126_t,<br>            report_390.cluster_1_127_t,<br>            report_390.cluster_1_128_t,<br>            report_390.cluster_1_129_n,<br>            report_390.cluster_1_130_t,<br>            report_390.cluster_1_131_t,<br>            report_390.cluster_1_132_n,<br>            report_390.cluster_1_133_n,<br>            report_390.cluster_1_134_n,<br>            report_390.cluster_1_135_n,<br>            report_390.cluster_1_136_n,<br>            report_390.cluster_1_137_t,<br>            report_390.cluster_1_138_t,<br>            report_390.cluster_1_139_n,<br>            report_390.cluster_1_140_n,<br>            report_390.cluster_1_141_n,<br>            report_390.cluster_1_142_n,<br>            report_390.cluster_1_143_n,<br>            report_390.cluster_1_144_t,<br>            report_390.cluster_1_145_t,<br>            report_390.cluster_1_146_t,<br>            report_390.cluster_1_147_t,<br>            report_390.cluster_1_148_n,<br>            report_390.cluster_1_149_d,<br>            report_390.cluster_1_150_n,<br>            report_390.cluster_1_151_t,<br>            report_390.cluster_1_154_d,<br>            report_390.cluster_1_155_t,<br>            report_390.cluster_1_156_t,<br>            report_390.cluster_1_157_t,<br>            report_390.cluster_1_159_d,<br>            report_390.cluster_1_160_t,<br>            report_390.cluster_1_161_d,<br>            report_390.cluster_1_162_t,<br>            report_390.cluster_1_163_d,<br>            report_390.cluster_1_164_t,<br>            report_390.cluster_1_165_t,<br>            report_390.cluster_1_166_t,<br>            report_390.cluster_1_167_t,<br>            report_390.cluster_1_168_t<br>           FROM report_390<br>          WHERE ((report_390.rep_top_id IN ( SELECT rep_top.rep_top_id<br>                   FROM rep_top<br>                  WHERE (rep_top.deleted = (0)::numeric))) AND (report_390.rep_top_id IN ( SELECT rep_current.rep_top_id<br>                   FROM rep_current)))) reporttable; |


