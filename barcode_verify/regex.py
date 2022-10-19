import re

parts = [
  {
    'name': 'AB1V Reaction Deisel',
    'part': '50-8670.6420',
    'regex': r"^V5SS(?P<year>\d\d)(?P<jdate>[0-3]\d\d)(?P<station>[1,2,3,4])(?P<sequence>\d{4})24046420$",
  },{
    'name': 'AB1V Reaction Gas',
    'part': '50-0450',
    'regex': r"^V5SS(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[1,2,3,4])(?<sequence>\d{4})24280450$",
  },{
    'name': 'AB1V Input Deisel',
    'part_number': '50-5401',
    'regex': r"^V3SS(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[1,2,3,4])(?<sequence>\d{4})24046418$",
  },{
    'name': 'AB1V Input Gas',
    'part': '50-0447',
    'regex': r"^V3SS(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[1,2,3,4])(?<sequence>\d{4})24280447$",
  },{
    'name': 'AB1V OverDrive Deisel',
    'part': '50-5404',
    'regex': r"^V6SS(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[1,2,3,4])(?<sequence>\d{4})24295404$",
  },{
    'name': 'AB1V OverDrive Gas',
    'part': '50-0519',
    'regex': r"^V6SS(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[1,2,3,4])(?<sequence>\d{4})24280519$",
  },{
    'name': '10R140 Gas',
    'part': '50-3214',
    'regex': r"^GTALB(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[0,1,2,3]0)(?<sequence>\d{4})LC3P 7D007 CB$",
  },{
    'name': '10R140 Diesel',
    'part': '50-5214',
    'regex': r"^GTALB(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[0,1,2,3]0)(?<sequence>\d{4})LC3P 7D007 BB$",
  },{
    'name': '10R80 Ford',
    'part': '50-9341',
    'regex': r"^GTALB(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[0,1,2,3]0)(?<sequence>\d{4})LC3P 7D007 BB$",
  },{
    'name': '10R60 Ford',
    'part': '50-0455',
    'regex': r"^GTALB(?<year>\d\d)(?<jdate>[0-3]\d\d)(?<station>[0,1,2,3]0)(?<sequence>\d{4})LC3P 7D007 BB$",
  },{
    'name': '10R80 GM',
    'part': '50-9341',
    'regex': r"^J6SS(?<year>\d)(?<jdate>[0-3]\d\d)(?<sequence>\d{4})Y7(?<station>[1,2,3,4])0$",
  },{
    'name': '10R60 GM',
    'part': '50-0455',
    'regex': r"^J6SS(?<year>\d)(?<jdate>[0-3]\d\d)(?<sequence>\d{4})X0(?<station>[1,2,3,4])0$",
  },
]

codes = [
  'V5SS223461001024046420',
  'V5SS2244610010240464204',
  '5SS0223461001024046420',
  'V5SS223461001024046421',
]


for code in codes: 
  print(parts[0]['regex'])
  result = re.search(parts[0]['regex'], code)
  if result:

    print(code, ': ', result.groups())
  else:
    print(code, "No Match")

"""
initial puns data incase I loose my db.
SET NAMES utf8mb4;

INSERT INTO `barcode_verify_barcodepun` (`id`, `name`, `part`, `regex`) VALUES
(1,	'AB1V Reaction Deisel',	'50-8670.6420',	'^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046420$'),
(2,	'AB1V Reaction Gas',	'50-0450',	'^V5SS(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[1,2,3,4])(?<sequence>\\d{4})24280450$'),
(3,	'AB1V Input Deisel',	'50-5401',	'^V3SS(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[1,2,3,4])(?<sequence>\\d{4})24046418$'),
(4,	'AB1V Input Gas',	'50-0447',	'^V3SS(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[1,2,3,4])(?<sequence>\\d{4})24280447$'),
(5,	'AB1V OverDrive Deisel',	'50-5404',	'^V6SS(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[1,2,3,4])(?<sequence>\\d{4})24295404$'),
(6,	'AB1V OverDrive Gas',	'50-0519',	'^V6SS(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[1,2,3,4])(?<sequence>\\d{4})24280519$'),
(7,	'10R140 Gas',	'50-3214',	'^GTALB(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[0,1,2,3]0)(?<sequence>\\d{4})LC3P 7D007 CB$'),
(8,	'10R140 Diesel',	'50-5214',	'^GTALB(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[0,1,2,3]0)(?<sequence>\\d{4})LC3P 7D007 BB$'),
(9,	'10R80 Ford',	'50-9341',	'^GTALB(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[0,1,2,3]0)(?<sequence>\\d{4})LC3P 7D007 BB$'),
(10,	'10R60 Ford',	'50-0455',	'^GTALB(?<year>\\d\\d)(?<jdate>[0-3]\\d\\d)(?<station>[0,1,2,3]0)(?<sequence>\\d{4})LC3P 7D007 BB$'),
(11,	'10R80 GM',	'50-9341',	'^J6SS(?<year>\\d)(?<jdate>[0-3]\\d\\d)(?<sequence>\\d{4})Y7(?<station>[1,2,3,4])0$'),
(12,	'10R60 GM',	'50-0455',	'^J6SS(?<year>\\d)(?<jdate>[0-3]\\d\\d)(?<sequence>\\d{4})X0(?<station>[1,2,3,4])0$');

"""

"""
sample data for varios parts
AB1V Input Deisel  V3SS220011000224046418 V3SS220011000324046418 V3SS220011000424046418

AB1V Reaction Deisel  V5SS220011000224046420 V5SS220011000324046420 V5SS220011000424046420



"""
