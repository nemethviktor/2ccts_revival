import pandas as pd
import os
import warnings

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def is_true(val) -> bool:
    """ Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == 'TRUE') or (val == 1)


def get_voltage_suffix(row):
    """
    Analyzes track columns to return specific technical suffixes.
    Returns 'Dual Pickup' if both rail-based and wire-based power is detected.
    """
    # 1. Get all active track columns
    track_cols = [c for c in row.index if c.startswith(
        'TRACK_TYPE_') and is_true(row[c])]

    # 2. Categorize the power sources based on the last segment of the column name
    # Wire-based (Pantograph)
    wires = [c for c in track_cols if any(v in c.split(
        '_')[-1] for v in ['25KV', '15KV', '3KV', '1500V', 'OHLE'])]
    # Rail-based (Contact shoe)
    rails = [c for c in track_cols if any(
        v in c.split('_')[-1] for v in ['3RD', '4TH'])]
    # Separately confirmed 'DUAL'
    hc_dual = [c for c in track_cols if any(
        v in c.split('_')[-1] for v in ['DUAL'])]

    # 3. Dual Pickup Logic: If we have both Wires and Rails active
    if (wires and rails) or hc_dual:
        return "Dual Pickup"

    # 4. Multi-voltage Logic: If we have multiple types within the same category
    if len(wires + rails) > 1:
        return "Multi-V"

    # 5. Individual Mapping (only reached if exactly one power type exists)
    mapping = {
        '25KV':  "25kV AC",
        '15KV':  "15kV AC",
        '3KV':   "3kV DC",
        '1500V': "1500V DC",
        '3RD':   "3rd Rail",
        '4TH':   "4th Rail",
        'OHLE':  "OHLE [Multi-V]"
    }

    # Combine lists to find the single active key
    active_power_types = wires + rails
    if active_power_types:
        tag = active_power_types[0].split('_')[-1]
        return mapping.get(tag, "")

    return ""


def get_hardcoded_content():
    content = []
    content.append("##grflangid 0x01\n\n")
    content.append("# Main grf title and description\n")
    content.append("STR_GRF_NAME                        :{TITLE}\n")
    content.append(
        "STR_GRF_DESCRIPTION                 :{SILVER}2cc Trains of the World in NML {}{}(c)2ccts Revival {}License:GPLv2 or higher. {}See readme for details.\n")
    content.append(
        "STR_GRF_URL                         :https://github.com/nemethviktor/2ccts_revival\n\n")
    content.append(f"""# General error messages
str_used_with_dynamic_engines       :dynamic_engines = true (setting in openttd.cfg)
str_error_region                    :No regions enabled, {{STRING}} has been disabled

# parameter strings
STR_PARAM_PURCHASE_COST             :Purchase cost multiplier
STR_PARAM_PURCHASE_COST_DESC        :You can use this setting to increase or decrease the purchase costs of the vehicles in this set.
STR_PARAM_RUNNING_COST              :Running cost multiplier
STR_PARAM_RUNNING_COST_DESC         :You can use this setting to increase or decrease the running costs of the vehicles in this set.

STR_PARAM_DIVIDE_16                 :1/16
STR_PARAM_DIVIDE_8                  :1/8
STR_PARAM_DIVIDE_4                  :1/4
STR_PARAM_DIVIDE_2                  :1/2
STR_PARAM_NORMAL                    :1 (default)
STR_PARAM_TIMES_2                   :2
STR_PARAM_TIMES_4                   :4
STR_PARAM_TIMES_8                   :8
STR_PARAM_TIMES_16                  :16

# region parameters
STR_PARAM_CONCEPT                                               :Concept vehicles
STR_PARAM_CONCEPT_DESC                                          :Use concept vehicles
STR_PARAM_REGION_AFRICA                                         :Africa
STR_PARAM_REGION_AFRICA_DESC                                    :Use vehicles from Africa
STR_PARAM_REGION_NORTH_AMERICA                                  :North America
STR_PARAM_REGION_NORTH_AMERICA_DESC                             :Use vehicles from North America
STR_PARAM_REGION_SOUTH_AMERICA                                  :South America
STR_PARAM_REGION_SOUTH_AMERICA_DESC                             :Use vehicles from South America
STR_PARAM_REGION_ASIA                                           :Asia
STR_PARAM_REGION_ASIA_DESC                                      :Use vehicles from Asia
STR_PARAM_REGION_NORTHERN_EUROPE                                :Northern Europe
STR_PARAM_REGION_NORTHERN_EUROPE_DESC                           :Use vehicles from Northern Europe
STR_PARAM_REGION_EASTERN_EUROPE                                 :Eastern Europe
STR_PARAM_REGION_EASTERN_EUROPE_DESC                            :Use vehicles from Eastern Europe
STR_PARAM_REGION_SOUTHERN_EUROPE                                :Southern Europe
STR_PARAM_REGION_SOUTHERN_EUROPE_DESC                           :Use vehicles from Southern Europe
STR_PARAM_REGION_WESTERN_EUROPE                                 :Western Europe
STR_PARAM_REGION_WESTERN_EUROPE_DESC                            :Use vehicles from Western Europe
STR_PARAM_REGION_OCEANIA                                        :Oceania
STR_PARAM_REGION_OCEANIA_DESC                                   :Use vehicles from Oceania

# loading speed parameter
STR_PARAM_LOADINGSPEED                                          :Loading speed
STR_PARAM_LOADINGSPEED_DESC                                     :Set the loading speed of this set
STR_PARAM_LOADINGSPEED_SLOW                                     :Slow
STR_PARAM_LOADINGSPEED_NORMAL                                   :Normal (default)
STR_PARAM_LOADINGSPEED_FAST                                     :Fast
STR_PARAM_LOADINGSPEED_ULTRA                                    :As fast as possible

# The following hardcoded values are entirely fron the newbadges set as-is
# Class names
STR_CLASS_FLAG                                                  :Country/Region
STR_CLASS_ROLE                                                  :Role
STR_CLASS_OPERATOR                                              :Operator
STR_CLASS_PROPULSION                                            :Propulsion
STR_CLASS_LIVERY                                                :Livery
STR_CLASS_REGION                                                :Region
STR_CLASS_ZONE                                                  :Zone

# Roles                 
STR_ROLE_PASSENGER                                              :Passenger
STR_ROLE_FREIGHT                                                :Freight
STR_ROLE_MIXED                                                  :Mixed
STR_ROLE_EXPRESS_PASSENGER                                      :Express passenger
STR_ROLE_EXPRESS_FREIGHT                                        :Express freight
STR_ROLE_HEAVY_FREIGHT                                          :Heavy freight
STR_ROLE_LIGHT_FREIGHT                                          :Light freight
STR_ROLE_MAIL                                                   :Mail
STR_ROLE_RESTAURANT_CAR                                         :Restaurant car
STR_ROLE_SHUNTING                                               :Shunting
STR_ROLE_BANKING                                                :Banking
STR_ROLE_SNOWPLOUGH                                             :Snowplough
STR_ROLE_UTILITY                                                :Utility
STR_ROLE_PROTOTYPE                                              :Prototype

# Regions
STR_REGION_AMERICA                                              :Americas
STR_REGION_AMERICA_NORTHERN                                     :Northern America
STR_REGION_AMERICA_CENTRAL                                      :Central America
STR_REGION_AMERICA_SOUTH                                        :South America
STR_REGION_AMERICA_CARIBBEAN                                    :Caribbean
STR_REGION_EUROPE                                               :Europe
STR_REGION_EUROPE_NORTHERN                                      :Northern Europe
STR_REGION_EUROPE_WESTERN                                       :Western Europe
STR_REGION_EUROPE_SOUTHERN                                      :Southern Europe
STR_REGION_EUROPE_EASTERN                                       :Eastern Europe
STR_REGION_AFRICA                                               :Africa
STR_REGION_AFRICA_NORTHERN                                      :Northern Africa
STR_REGION_AFRICA_WESTERN                                       :Western Africa
STR_REGION_AFRICA_MIDDLE                                        :Middle Africa
STR_REGION_AFRICA_EASTERN                                       :Eastern Africa
STR_REGION_AFRICA_SOUTHERN                                      :Southern Africa
STR_REGION_ASIA                                                 :Asia
STR_REGION_ASIA_WESTERN                                         :Western Asia
STR_REGION_ASIA_CENTRAL                                         :Central Asia
STR_REGION_ASIA_EASTERN                                         :Eastern Asia
STR_REGION_ASIA_SOUTHERN                                        :Southern Asia
STR_REGION_ASIA_SOUTHEASTERN                                    :South-eastern Asia
STR_REGION_OCEANIA                                              :Oceania
STR_REGION_OCEANIA_MICRONESIA                                   :Micronesia
STR_REGION_OCEANIA_MELANESIA                                    :Melanesia
STR_REGION_OCEANIA_POLYNESIA                                    :Polynesia
STR_REGION_OCEANIA_AUSTRALIA_AND_NEW_ZEALAND                    :Australia and New Zealand

# Residential, Commercial and Industrial
STR_ZONE_RESIDENTIAL                                            :Residential
STR_ZONE_RESIDENTIAL_LOW_DENSITY                                :Low density residential
STR_ZONE_RESIDENTIAL_MEDIUM_DENSITY                             :Medium density residential
STR_ZONE_RESIDENTIAL_HIGH_DENSITY                               :High density residential
STR_ZONE_COMMERCIAL                                             :Commercial
STR_ZONE_COMMERCIAL_LOW_DENSITY                                 :Low density commercial
STR_ZONE_COMMERCIAL_MEDIUM_DENSITY                              :Medium density commercial
STR_ZONE_COMMERCIAL_HIGH_DENSITY                                :High density commercial
STR_ZONE_INDUSTRIAL                                             :Industrial
STR_ZONE_INDUSTRIAL_LOW_DENSITY                                 :Low density industrial
STR_ZONE_INDUSTRIAL_MEDIUM_DENSITY                              :Medium density industrial
STR_ZONE_INDUSTRIAL_HIGH_DENSITY                                :High density industrial
STR_ZONE_MIXED                                                  :Commercial & residential
STR_ZONE_MIXED_LOW_DENSITY                                      :Low density commercial & residential
STR_ZONE_MIXED_MEDIUM_DENSITY                                   :Medium density commercial & residential
STR_ZONE_MIXED_HIGH_DENSITY                                     :High density commercial & residential
STR_ZONE_AGRICULTURAL                                           :Agricultural
STR_ZONE_FORESTRY                                               :Forestry
STR_ZONE_PUBLIC                                                 :Public
STR_ZONE_TRANSPORT                                              :Transport
STR_ZONE_GENERAL                                                :General
STR_ZONE_LEISURE                                                :Leisure
STR_ZONE_OTHER                                                  :Other

# Country flags
STR_FLAG                                                        :Flag
STR_FLAG_AD                                                     :Andorra
STR_FLAG_AE                                                     :United Arab Emirates
STR_FLAG_AF                                                     :Afghanistan
STR_FLAG_AG                                                     :Antigua and Barbuda
STR_FLAG_AI                                                     :Anguilla
STR_FLAG_AL                                                     :Albania
STR_FLAG_AM                                                     :Armenia
STR_FLAG_AO                                                     :Angola
STR_FLAG_AQ                                                     :Antarctica
# STR_FLAG_ARA                                                    :Arab League
STR_FLAG_AR                                                     :Argentina
STR_FLAG_AS                                                     :American Samoa
STR_FLAG_AT                                                     :Austria
STR_FLAG_AU                                                     :Australia
STR_FLAG_AW                                                     :Aruba
STR_FLAG_AX                                                     :Åland
STR_FLAG_AZ                                                     :Azerbaijan
STR_FLAG_BA                                                     :Bosnia and Herzegovina
STR_FLAG_BB                                                     :Barbados
STR_FLAG_BD                                                     :Bangladesh
STR_FLAG_BE                                                     :Belgium
STR_FLAG_BF                                                     :Burkina Faso
STR_FLAG_BG                                                     :Bulgaria
STR_FLAG_BH                                                     :Bahrain
STR_FLAG_BI                                                     :Burundi
STR_FLAG_BJ                                                     :Benin
STR_FLAG_BL                                                     :Saint Barthélemy
STR_FLAG_BM                                                     :Bermuda
STR_FLAG_BN                                                     :Brunei
STR_FLAG_BO                                                     :Bolivia
STR_FLAG_BQ                                                     :Caribbean Netherlands
STR_FLAG_BR                                                     :Brazil
STR_FLAG_BS                                                     :Bahamas
STR_FLAG_BT                                                     :Bhutan
STR_FLAG_BV                                                     :Bouvet Island
STR_FLAG_BW                                                     :Botswana
STR_FLAG_BY                                                     :Belarus
STR_FLAG_BZ                                                     :Belize
STR_FLAG_CA                                                     :Canada
STR_FLAG_CC                                                     :Cocos Islands
STR_FLAG_CD                                                     :Democratic Republic of the Congo
# STR_FLAG_CEF                                                    :(Central European Free Trade Agreement)
STR_FLAG_CF                                                     :Central African Republic
STR_FLAG_CG                                                     :Republic of the Congo
STR_FLAG_CH                                                     :Switzerland
STR_FLAG_CI                                                     :Ivory Coast
STR_FLAG_CK                                                     :Cook Islands
STR_FLAG_CL                                                     :Chile
STR_FLAG_CM                                                     :Cameroon
STR_FLAG_CN                                                     :China
STR_FLAG_CO                                                     :Colombia
# STR_FLAG_CP                                                     :(Clipperton Island)
STR_FLAG_CR                                                     :Costa Rica
STR_FLAG_CU                                                     :Cuba
STR_FLAG_CV                                                     :Cape Verde
STR_FLAG_CW                                                     :Curaçao
STR_FLAG_CX                                                     :Christmas Island
STR_FLAG_CY                                                     :Cyprus
STR_FLAG_CZ                                                     :Czech Republic
STR_FLAG_DE                                                     :Germany
# STR_FLAG_DG                                                     :(Diego Garcia)
STR_FLAG_DJ                                                     :Djibouti
STR_FLAG_DK                                                     :Denmark
STR_FLAG_DM                                                     :Dominica
STR_FLAG_DO                                                     :Dominican Republic
STR_FLAG_DZ                                                     :Algeria
# STR_FLAG_EAC                                                    :(East African Community)
STR_FLAG_EC                                                     :Ecuador
STR_FLAG_EE                                                     :Estonia
STR_FLAG_EG                                                     :Egypt
STR_FLAG_EH                                                     :Western Sahara
STR_FLAG_ER                                                     :Eritrea
# STR_FLAG_ESC                                                    :Spain (Catalonia)
# STR_FLAG_ESG                                                    :Spain (Galicia)
# STR_FLAG_ESP                                                    :Spain (Basque Country)
STR_FLAG_ES                                                     :Spain
STR_FLAG_ET                                                     :Ethiopia
STR_FLAG_EU                                                     :European Union
STR_FLAG_FI                                                     :Finland
STR_FLAG_FJ                                                     :Fiji
STR_FLAG_FK                                                     :Falkland Islands
STR_FLAG_FM                                                     :Micronesia
STR_FLAG_FO                                                     :Faroe Islands
STR_FLAG_FR                                                     :France
STR_FLAG_GA                                                     :Andorra
# STR_FLAG_GBE                                                    :England
# STR_FLAG_GBN                                                    :Northern Ireland
# STR_FLAG_GBS                                                    :Scotland
STR_FLAG_GB                                                     :United Kingdom
# STR_FLAG_GBW                                                    :Wales
STR_FLAG_GD                                                     :Grenada
STR_FLAG_GE                                                     :Georgia
STR_FLAG_GF                                                     :French Guiana
STR_FLAG_GG                                                     :Guernsey
STR_FLAG_GH                                                     :Ghana
STR_FLAG_GI                                                     :Gibraltar
STR_FLAG_GL                                                     :Greenland
STR_FLAG_GM                                                     :Gambia
STR_FLAG_GN                                                     :Guinea
STR_FLAG_GP                                                     :Guadeloupe
STR_FLAG_GQ                                                     :Equatorial Guinea
STR_FLAG_GR                                                     :Greece
STR_FLAG_GS                                                     :South Georgia and the South Sandwich Islands
STR_FLAG_GT                                                     :Gautemala
STR_FLAG_GU                                                     :Guam
STR_FLAG_GW                                                     :Guinea-Bissau
STR_FLAG_GY                                                     :Guyana
STR_FLAG_HK                                                     :Hong Kong
STR_FLAG_HM                                                     :Heard Island and McDonald Islands
STR_FLAG_HN                                                     :Honduras
STR_FLAG_HR                                                     :Croatia
STR_FLAG_HT                                                     :Haiti
STR_FLAG_HU                                                     :Hungary
# STR_FLAG_IC                                                     :Canary Islands
STR_FLAG_ID                                                     :Indonesia
STR_FLAG_IE                                                     :Ireland
STR_FLAG_IL                                                     :Israel
STR_FLAG_IM                                                     :Isle of Man
STR_FLAG_IN                                                     :India
STR_FLAG_IO                                                     :British Indian Ocean Territory
STR_FLAG_IQ                                                     :Iraq
STR_FLAG_IR                                                     :Iran
STR_FLAG_IS                                                     :Iceland
STR_FLAG_IT                                                     :Italy
STR_FLAG_JE                                                     :Jersey
STR_FLAG_JM                                                     :Jamaica
STR_FLAG_JO                                                     :Jordan
STR_FLAG_JP                                                     :Japan
STR_FLAG_KE                                                     :Kenya
STR_FLAG_KG                                                     :Kyrgyzstan
STR_FLAG_KH                                                     :Cambodia
STR_FLAG_KI                                                     :Kiribati
STR_FLAG_KM                                                     :Comoros
STR_FLAG_KN                                                     :Saint Kitts and Nevis
STR_FLAG_KP                                                     :North Korea
STR_FLAG_KR                                                     :South Korea
STR_FLAG_KW                                                     :Kuwait
STR_FLAG_KY                                                     :Cayman Islands
STR_FLAG_KZ                                                     :Kazakhstan
STR_FLAG_LA                                                     :Lao
STR_FLAG_LB                                                     :Lebanon
STR_FLAG_LC                                                     :Saint Lucia
STR_FLAG_LI                                                     :Liechtenstein
STR_FLAG_LK                                                     :Sri Lanka
STR_FLAG_LR                                                     :Liberia
STR_FLAG_LS                                                     :Lesotho
STR_FLAG_LT                                                     :Lithuania
STR_FLAG_LU                                                     :Luxembourg
STR_FLAG_LV                                                     :Lativa
STR_FLAG_LY                                                     :Libya
STR_FLAG_MA                                                     :Morocco
STR_FLAG_MC                                                     :Monaco
STR_FLAG_MD                                                     :Moldova
STR_FLAG_ME                                                     :Montenegro
STR_FLAG_MF                                                     :Saint Martin
STR_FLAG_MG                                                     :Madagascar
STR_FLAG_MH                                                     :Marshall Islands
STR_FLAG_MK                                                     :North Macedonia
STR_FLAG_ML                                                     :Mali
STR_FLAG_MM                                                     :Myanmar
STR_FLAG_MN                                                     :Mongolia
STR_FLAG_MO                                                     :Macao
STR_FLAG_MP                                                     :Northern Mariana Islands
STR_FLAG_MQ                                                     :Martinique
STR_FLAG_MR                                                     :Mauritania
STR_FLAG_MS                                                     :Montserrat
STR_FLAG_MT                                                     :Malta
STR_FLAG_MU                                                     :Mauritius
STR_FLAG_MV                                                     :Maldives
STR_FLAG_MW                                                     :Malawi
STR_FLAG_MX                                                     :Mexico
STR_FLAG_MY                                                     :Malaysia
STR_FLAG_MZ                                                     :Mozambique
STR_FLAG_NA                                                     :Namibia
STR_FLAG_NC                                                     :New Caledonia
STR_FLAG_NE                                                     :Niger
STR_FLAG_NF                                                     :Norfolk Island
STR_FLAG_NG                                                     :Nigeria
STR_FLAG_NI                                                     :Nicaragua
STR_FLAG_NL                                                     :Netherlands
STR_FLAG_NO                                                     :Norway
STR_FLAG_NP                                                     :Nepal
STR_FLAG_NR                                                     :Nauru
STR_FLAG_NU                                                     :Niue
STR_FLAG_NZ                                                     :New Zealand
STR_FLAG_OM                                                     :Oman
STR_FLAG_PA                                                     :Panama
# STR_FLAG_PC                                                     :(Pacific Community)
STR_FLAG_PE                                                     :Peru
STR_FLAG_PF                                                     :French Polynesia
STR_FLAG_PG                                                     :Papua New Guinea
STR_FLAG_PH                                                     :Philippines
STR_FLAG_PK                                                     :Pakistan
STR_FLAG_PL                                                     :Poland
STR_FLAG_PM                                                     :Saint Pierre and Miquelon
STR_FLAG_PN                                                     :Pitcairn
STR_FLAG_PR                                                     :Puerto Rico
STR_FLAG_PS                                                     :Palestine
STR_FLAG_PT                                                     :Portugal
STR_FLAG_PW                                                     :Palau
STR_FLAG_PY                                                     :Paraguay
STR_FLAG_QA                                                     :Qatar
STR_FLAG_RE                                                     :Réunion
STR_FLAG_RO                                                     :Romania
STR_FLAG_RS                                                     :Serbia
STR_FLAG_RU                                                     :Russia
STR_FLAG_RW                                                     :Rwanda
STR_FLAG_SA                                                     :Saudi Arabia
STR_FLAG_SB                                                     :Solomon Islands
STR_FLAG_SC                                                     :Seychelles
STR_FLAG_SD                                                     :Sudan
STR_FLAG_SE                                                     :Sweden
STR_FLAG_SG                                                     :Singapore
# STR_FLAG_SHA                                                    :Ascension Island
# STR_FLAG_SHH                                                    :Saint Helena
STR_FLAG_SH                                                     :Saint Helena, Ascension and Tristan da Cunha
# STR_FLAG_SHT                                                    :Tristan da Cunha
STR_FLAG_SI                                                     :Slovenia
STR_FLAG_SJ                                                     :Svalbard and Jan Mayen
STR_FLAG_SK                                                     :Slovakia
STR_FLAG_SL                                                     :Sierra Leone
STR_FLAG_SM                                                     :San Marino
STR_FLAG_SN                                                     :Senegal
STR_FLAG_SO                                                     :Somalia
STR_FLAG_SR                                                     :Suriname
STR_FLAG_SS                                                     :South Sudan
STR_FLAG_ST                                                     :Sao Tome and Principe
STR_FLAG_SV                                                     :El Salvador
STR_FLAG_SX                                                     :Sint Maarten
STR_FLAG_SY                                                     :Syrian Arab Republic
STR_FLAG_SZ                                                     :Eswatini
STR_FLAG_TC                                                     :Turks and Caicos Islands
STR_FLAG_TD                                                     :Chad
STR_FLAG_TF                                                     :French Southern Territories
STR_FLAG_TG                                                     :Togo
STR_FLAG_TH                                                     :Thailand
STR_FLAG_TJ                                                     :Tajikistan
STR_FLAG_TK                                                     :Tokelau
STR_FLAG_TL                                                     :Timor-Leste
STR_FLAG_TM                                                     :Turkmenistan
STR_FLAG_TN                                                     :Tunisia
STR_FLAG_TO                                                     :Tonga
STR_FLAG_TR                                                     :Türkiye
STR_FLAG_TT                                                     :Trinidad and Tobago
STR_FLAG_TV                                                     :Tuvalu
STR_FLAG_TW                                                     :Taiwan
STR_FLAG_TZ                                                     :Tanzania
STR_FLAG_UA                                                     :Ukraine
STR_FLAG_UG                                                     :Uganda
STR_FLAG_UM                                                     :United States Minor Outlying Islands
# STR_FLAG_UN                                                     :(United Nations)
STR_FLAG_US                                                     :United States
STR_FLAG_UY                                                     :Uruguay
STR_FLAG_UZ                                                     :Uzbekistan
STR_FLAG_VA                                                     :Holy See
STR_FLAG_VC                                                     :Saint Vincent and the Grenadines
STR_FLAG_VE                                                     :Venezuela
STR_FLAG_VG                                                     :Virgin Islands (British)
STR_FLAG_VI                                                     :Virgin Islands (U.S.)
STR_FLAG_VN                                                     :Vietnam
STR_FLAG_VU                                                     :Vanuatu
STR_FLAG_WF                                                     :Wallis and Futuna
STR_FLAG_WS                                                     :Samoa
# STR_FLAG_XK                                                     :Kosovo
# STR_FLAG_XX                                                     :(Unknown)
STR_FLAG_YE                                                     :Yemen
STR_FLAG_YT                                                     :Mayotte
STR_FLAG_ZA                                                     :South Africa
STR_FLAG_ZM                                                     :Zambia
STR_FLAG_ZW                                                     :Zimbabwe

# Historical flags                                          
STR_FLAG_YU                                                     :Yugoslavia
STR_FLAG_GDR                                                    :East Germany
STR_FLAG_SU                                                     :USSR
STR_FLAG_EUROPE                                                 :Europe
STR_FLAG_WRLD                                                   :World

# Power types
STR_POWER                                                       :Power
STR_POWER_STEAM                                                 :Steam
STR_POWER_DIESEL                                                :Diesel
STR_POWER_DIESEL_ELECTRIC                                       :Diesel (Diesel-electric)
STR_POWER_DIESEL_HYDRAULIC                                      :Diesel (Diesel-hydraulic)
STR_POWER_ELECTRIC                                              :Electric
STR_POWER_ELECTRIC_AC                                           :Electric (AC)
STR_POWER_ELECTRIC_AC_15                                        :Electric (AC 15kV)
STR_POWER_ELECTRIC_AC_25                                        :Electric (AC 25kV)
STR_POWER_ELECTRIC_DC                                           :Electric (DC)
STR_POWER_ELECTRIC_DC_600                                       :Electric (DC 600V)
STR_POWER_ELECTRIC_DC_750                                       :Electric (DC 750V)
STR_POWER_ELECTRIC_DC_1200                                      :Electric (DC 1200V)
STR_POWER_ELECTRIC_DC_1500                                      :Electric (DC 1500V)
STR_POWER_ELECTRIC_DC_3000                                      :Electric (DC 3kV)
STR_POWER_TURBINE                                               :Gas Turbine
STR_POWER_BATTERY                                               :Battery
STR_POWER_MAGLEV                                                :Maglev
STR_POWER_METRO                                                 :Metro

# Colours
STR_LIVERY_COMPANY_2CC                                          :Dual company colour (2CC)
STR_LIVERY_COMPANY_RANDOM_1CC                                   :Random based on first company colour
STR_LIVERY_COMPANY_RANDOM_2CC                                   :Random based on second company colour

# VEHICLE NAMES""")
    return content


def generate_english_lng():
    print("--- Generating English Language File ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.join(project_root, 'lang', 'english.lng')

    # Load Data
    sheets = pd.read_excel(excel_path, sheet_name=None)
    df_items = sheets['control']

    # We need track_types and properties to determine the full suffix
    df_props = sheets['properties'][['VEHIDCODE',
                                     'COST_CAT', 'ENGINE_CLASS', 'IS_TURBINE']]
    df_tracks = sheets['track_types']

    # Merge everything
    df_master = pd.merge(df_items, df_props, on='VEHIDCODE', how='left')
    df_master = pd.merge(df_master, df_tracks, on='VEHIDCODE', how='left')

    # Base Suffix Map for General Types
    base_suffixes = {
        'STEAMENGINE': '(Steam)',
        'DIESELENGINE': '(Diesel)',
        'ELECTRICENGINE': '(Electric)',
        'MAGLEVSU': '(Maglev)',
        'STEAMRAILBUS': '(Steam Railbus)',
        'DIESELRAILBUS': '(Diesel Railbus)',
        'ELECTRICRAILBUS': '(Electric Railbus)',
        'METRORAILBUS': '(Single Unit Metro)',
        'MAGLEVRAILBUS': '(Maglev Railbus)',
        'DMU': '(DMU)',
        'EMU': '(EMU)',
        'MAGLEVMU': '(MMU)',
        'COACH': '(Coach)',
        'WAGON': '(Wagon)',
        'METRO': '(Metro)',
    }

    # 2. Hardcoded Header (Top of your current file)
    content = get_hardcoded_content()

    # 3. Process Vehicles
    # Group by COST_CAT to keep the file organized like the original
    # Process by COST_CAT for organization
    for cat in df_master['COST_CAT'].unique():
        if pd.isna(cat):
            continue

        content.append(f"\n# {cat}\n")
        cat_df = df_master[df_master['COST_CAT'] == cat]

        for _, row in cat_df.iterrows():
            vehid = str(row['VEHIDCODE']).lower()
            base_name = row['ENGLISH']

            # 1. Get Base Type Suffix
            suffix = base_suffixes.get(row['COST_CAT'], f"({row['COST_CAT']})")
            if is_true(row['IS_TURBINE']):
                suffix = "(Gas Turbine)"

            # 2. Add Voltage Specifics if it is Electric
            if row['ENGINE_CLASS'] == 'ELECTRIC' or cat == 'METRO':
                v_suffix = get_voltage_suffix(row)
                if v_suffix:
                    # e.g. (Electric) -> (Electric, 25kV AC)
                    suffix = suffix.replace(')', f", {v_suffix})")
            # For these two we just wipe the previous suffix element because it too verbose otherwise
            if vehid.lower().endswith('unpowered'):
                suffix = "(Unpowered)"
            elif vehid.lower().endswith('powered'):
                suffix = "(Powered)"

            label = f"str_{vehid}"
            line = f"{label:<70}:{base_name} {suffix}\n"
            content.append(line)

    content.append("\n# PURCHASE MENU TEXTS\n")
    content.append(
        "str_unit_wagon_passenger        :This generic wagon can ONLY be used with passenger MUs to create trains of the desired length\n")
    content.append(
        "str_unit_wagon_cargo            :This generic wagon can ONLY be used with cargo MUs to create trains of the desired length\n\n")

    content.append("# Can(not) attach vehicle texts\n")
    content.append(
        "str_cannot_attach_wagon_to_MU                           :Cannot attach wagon to Multiple Unit engine\n")
    content.append(
        "str_cannot_attach_wagon_to_Unit_Wagon                   :Cannot attach regular wagon to Unit Wagon\n")
    content.append(
        "str_cannot_attach_Unit_wagon_to_engine                  :Cannot attach Unit Wagon to regular engine\n")
    content.append(
        "str_cannot_attach_Unit_wagon_to_wagon                   :Cannot attach Unit Wagon to regular wagon\n")
    content.append(
        "str_cannot_attach_Unit_wagon_cargo_to_passenger         :Cannot attach cargo Unit Wagon to passenger Multiple Unit engine\n")
    content.append(
        "str_cannot_attach_Unit_wagon_passenger_to_cargo         :Cannot attach passenger Unit Wagon to cargo Multiple Unit engine\n")

    # 5. Save File
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(content)

    print(f"Successfully generated {output_path}")


if __name__ == "__main__":
    generate_english_lng()
    print("--- Generating English Language File Finished ---")
