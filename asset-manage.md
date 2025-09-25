###################################################################################################################################
###以下部分介绍如何从exascaler.toml文件中抽取信息构建设备资产台账以及如何查询的相关代码、及操作方法#######################################
###generate_cluster_yaml.py：从exascaler.toml文件中抽取信息，部分数据不全，需要从控制器的SSSA信息抓取###################################
###generate_cluster_yaml.py：对台账文件进行查询，可指定参数文件，列示集群中的设备数量、SFA版本、EXA版本、BBU过期时间、控制器序列号等等######
###注：在台账文件中只保留首行clusters:，如果将多个台账文件合并在一起，将多余的这一行去掉##################################################
####################################################################################################################################
##依赖库：需要toml和pyyaml库，可通过以下命令安装：##
pip install toml pyyaml

##Command sample##
python generate_cluster_yaml.py exascaler.cyberport.1su.toml -o Cyberport_1SU_clusters.yaml
python asset_analyze.py 
##以下为命令举例###
$ python generate_cluster_yaml.py exascaler.cyberport.1su.toml -o Cyberport_1SU_clusters.yaml 

已生成YAML文件: Cyberport_1SU_clusters.yaml

以下字段未从TOML中获取到，需后续手工补充：
1. 集群级字段: Capacity, Network_type, Network_port_type, Support_status, Asset_owner
2. 设备级字段: CP2-DDN-OSS-01:type, CP2-DDN-OSS-01:SFA version, CP2-DDN-OSS-01:Capacity, CP2-DDN-OSS-01:Controller_c0_serial_number, CP2-DDN-OSS-01:Controller_c1_serial_number, CP2-DDN-OSS-01:BBU1_Mfg_Date, CP2-DDN-OSS-01:BBU2_Mfg_Date, CP2-DDN-OSS-02:type, CP2-DDN-OSS-02:SFA version, CP2-DDN-OSS-02:Capacity, CP2-DDN-OSS-02:Controller_c0_serial_number, CP2-DDN-OSS-02:Controller_c1_serial_number, CP2-DDN-OSS-02:BBU1_Mfg_Date, CP2-DDN-OSS-02:BBU2_Mfg_Date
3. 控制器级字段: CP2-DDN-OSS-01:Controller_c0_serial_number, CP2-DDN-OSS-01:Controller_c1_serial_number, CP2-DDN-OSS-02:Controller_c0_serial_number, CP2-DDN-OSS-02:Controller_c1_serial_number
carter@dcarter:~/asset/test$ 
carter@dcarter:~/asset/test$ more Cyberport_1SU_clusters.yaml 
clusters:
  - Cluster_name: D2_Cluster
    EXA version: 6.3.0
    Capacity: null
    Network_type: null
    Network_port_type: null
    EMF_IP: 10.20.0.89
    Support_status: null
    Asset_owner: null
    devices:
      - Device_name: CP2-DDN-OSS-01
        type: null
        SFA version: null
        Capacity: null
        Controller_c0_ip: 10.20.0.82
        Controller_c1_ip: 10.20.0.84
        Controller_c0_serial_number: null
        Controller_c1_serial_number: null
        BBU1_Mfg_Date: null
        BBU2_Mfg_Date: null
        Hosts:
          - hostname: CP2-DDN-OSS-01-MDS0
            role: MDS/OSS
            ip:
              management: 10.20.0.85
              lnet1_network: 10.24.255.1
              lnet2_network: 10.24.255.2
          - hostname: CP2-DDN-OSS-01-MDS1
            role: MDS/OSS
            ip:
              management: 10.20.0.86
              lnet1_network: 10.24.255.3
              lnet2_network: 10.24.255.4
          - hostname: CP2-DDN-OSS-01-MDS2
            role: MDS/OSS
            ip:
              management: 10.20.0.87
              lnet1_network: 10.24.255.5
              lnet2_network: 10.24.255.6
          - hostname: CP2-DDN-OSS-01-MDS3
            role: MDS/OSS
            ip:
              management: 10.20.0.88
              lnet1_network: 10.24.255.7
              lnet2_network: 10.24.255.8
      - Device_name: CP2-DDN-OSS-02
        type: null
        SFA version: null
        Capacity: null
        Controller_c0_ip: 10.20.0.91
        Controller_c1_ip: 10.20.0.93
        Controller_c0_serial_number: null
        Controller_c1_serial_number: null
        BBU1_Mfg_Date: null
        BBU2_Mfg_Date: null
        Hosts:
          - hostname: CP2-DDN-OSS-02-MDS0
            role: MDS/OSS
            ip:
              management: 10.20.0.94
              lnet1_network: 10.24.255.9
              lnet2_network: 10.24.255.10
          - hostname: CP2-DDN-OSS-02-MDS1
            role: MDS/OSS
            ip:
              management: 10.20.0.95
              lnet1_network: 10.24.255.11
              lnet2_network: 10.24.255.12
          - hostname: CP2-DDN-OSS-02-MDS2
            role: MDS/OSS
            ip:
              management: 10.20.0.96
              lnet1_network: 10.24.255.13
              lnet2_network: 10.24.255.14
          - hostname: CP2-DDN-OSS-02-MDS3
            role: MDS/OSS
            ip:
              management: 10.20.0.97
              lnet1_network: 10.24.255.15
              lnet2_network: 10.24.255.16
$cat Cyberport_1SU_clusters.yaml >> asset_ddn_clusters.yaml
##注意将多余的首行“clusters:”去除，可以手动补充台账中缺失的信息######

##############asset_analyze.py用法举例##############################
$ python asset_analyze.py 

===== Cluster Management System =====
0. Load YAML file
1. List device count per cluster
2. List SFA version details
3. List EXA version details
4. Calculate BBU expiration dates
5. Query cluster capacity
6. Query device serial numbers
7. Exit
Enter your choice (0-7): 0
Enter YAML file path: asset_ddn_clusters.yaml
Successfully loaded 7 clusters from asset_ddn_clusters.yaml

===== Cluster Management System =====
0. Load YAML file
   Current file: asset_ddn_clusters.yaml
1. List device count per cluster
2. List SFA version details
3. List EXA version details
4. Calculate BBU expiration dates
5. Query cluster capacity
6. Query device serial numbers
7. Exit
Enter your choice (0-7): 1
Enter Asset_owner name to query (leave empty for all): 

Cluster Name         Count      Asset Owner    
--------------------------------------------------
D1_Cluster           1          BYD            
D2_Cluster           2          BYD            
F1_Cluster           2          BYD            
F3_Cluster           6          BYD            
D2_object            3          BYD            
D2_Cluster           2          Cyberport      
D2_Cluster           9          Cyberport      

Total Devices:       25        

===== Cluster Management System =====
0. Load YAML file
   Current file: asset_ddn_clusters.yaml
1. List device count per cluster
2. List SFA version details
3. List EXA version details
4. Calculate BBU expiration dates
5. Query cluster capacity
6. Query device serial numbers
7. Exit
Enter your choice (0-7): 2
Enter Asset_owner name to query (leave empty for all): 

Cluster Name         Device Name          Asset Owner     SFA Version     Type      
-------------------------------------------------------------------------------------
D1_Cluster           BYD-AI400X2-2        BYD             12.7.0          AI400X2   
D2_Cluster           BYD-AI400X2-1        BYD             12.7.0          AI400X2   
D2_Cluster           BYD-AI400X2T-2       BYD             12.7.0          AI400X2T  
F1_Cluster           BYD-AI400X2-1        BYD             12.5.0          AI400X2   
F1_Cluster           BYD-AI400X2T-2       BYD             12.6.0.1        AI400X2T  
F3_Cluster           X2T-4F3D05-000       BYD             12.7.0          AI400X2T  
F3_Cluster           X2T-4F3D05-001       BYD             12.7.0          AI400X2T  
F3_Cluster           X2T-4F3D05-002       BYD             12.7.0          AI400X2T  
F3_Cluster           X2T-4F3D05-003       BYD             12.7.0          AI400X2T  
F3_Cluster           X2T-4F3D05-004       BYD             12.7.0          AI400X2T  
F3_Cluster           X2T-4F3D05-005       BYD             12.7.0          AI400X2T  
D2_object            BYDS3-1              BYD             12.5.0          AI400X2   
D2_object            BYDS3-2              BYD             12.5.0          AI400X2   
D2_object            BYDS3-3              BYD             12.5.0          AI400X2   
D2_Cluster           CP2-DDN-OSS-01       Cyberport       12.5.0          AI400X2   
D2_Cluster           CP2-DDN-OSS-02       Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-00               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-01               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-02               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-03               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-04               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-05               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-06               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-07               Cyberport       12.5.0          AI400X2   
D2_Cluster           CYB-08               Cyberport       12.5.0          AI400X2   

SFA Version Summary:
-------------------------
12.7.0: 9 device(s)
12.5.0: 15 device(s)
12.6.0.1: 1 device(s)

===== Cluster Management System =====
0. Load YAML file
   Current file: asset_ddn_clusters.yaml
1. List device count per cluster
2. List SFA version details
3. List EXA version details
4. Calculate BBU expiration dates
5. Query cluster capacity
6. Query device serial numbers
7. Exit
Enter your choice (0-7): 7
Exiting program.
carter@dcarter:~/asset/test$ 








##################字段注释#############
  - Cluster_name: ###仅用于信息标识。EXAScaler 本身不使用该名称，用于区分不同的集群安装实例。需手工输入。
    EXA version:  ###EXAScaler server版本，可自动生成
    Capacity:     ###集群总的可用容量，需手工输入。
    Network_type: ###网络类型，可取值：INFINIBAND | ETHERNET, 取值确认方法：app show ioc all
    Network_port_type: ###网络端口类型，常见取值：HDR200 | NDR200 | EDR100， 取值确认方法：ibstatus
    EMF_IP:       ### EMF的管理IP地址，可自动生成
    Support_status: ####集群的维保状态，常见取值：BSOS-Active | BSOS-Expired | BSOS-Future | PROS-Active | PROS-Expired | PROS-Future， 取值确认方法：查阅该客户的SFDC记录
    Asset_owner:  ###该设备的客户名称，需手工输入
    devices:
      - Device_name: ###控制器名称，可自动生成
        type:        ###控制器型号，常见取值：400NVX2 | 400NVX2T | 400X3 | 7990X，取值确认方法：cat SFA-NAME-c0.sssa.log | grep -i 'Platform' | awk '{print $2}' | sed 's/^SFA//;s/E$//'
        SFA version: ###SFA OS 版本，取值确认方法： show controller
        Capacity:    ###该设备的可用容量，取值确认方法：show vd，如果pool的Free Capacity比较多，可以相加计算。
        Controller_c0_ip: ###控制器C0的IP地址，可自动生成
        Controller_c1_ip: ###控制器C1的IP地址，可自动生成
        Controller_c0_serial_number: ###SFA控制器c0的序列号，字段取值方法： cat SFA-NAME-c0.sssa.log |grep -i 'Production Serial numb:' | awk '{print $4}'
        Controller_c1_serial_number: ###SFA控制器c1的序列号，字段取值方法： cat SFA-NAME-c0.sssa.log |grep -i 'Production Serial numb:' | awk '{print $4}'
        BBU1_Mfg_Date:    ###控制器的BBU生产时间，注意原始值类似“Sat Nov 16 2024”，去掉星期几，将后面的时间转换为简洁的数字形式，便于查看，比如：11/16/2024.字段取值方法：cat F3-2-X3-4F3-2-000.c0.sssa.log |grep -i 'Battery Mfg. Date'
        BBU2_Mfg_Date:    ###同上
        Expansion_enclosure_type: ###扩展柜类型，常见取值： SS9024 | SE2420
        Expansion_enclosure_number: ###扩展柜数量
        Hosts:
          - hostname:   ###VM name，可自动生成
            role:       ###VM 角色，可自动生成，常见取值： MDS | OSS | MDS/OSS
            ip:
              management: 10.17.210.17  ###VM的管理地址
              lnet1_network: 100.1.3.1  ###VM的lnet地址1
              lnet2_network: 100.1.3.2  ###VM的lnet地址2
