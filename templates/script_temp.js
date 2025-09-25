    <script>
        // YAML数据 - 用于在JavaScript中处理 (保留以备下载功能需要)
        const yamlData = {{ assets_info|tojson|safe }};
        
        // 在页面加载时初始化资产查询功能
        document.addEventListener('DOMContentLoaded', function() {
            // 加载资产所有者和集群名称
            loadAssetOwners();
            
            // 处理查询表单提交
            const form = document.getElementById('assetQueryForm');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(form);
                    const searchParams = new URLSearchParams(formData);
                    
                    // 显示加载指示器
                    const resultsContainer = document.getElementById('results-container');
                    resultsContainer.innerHTML = '<div style="text-align:center;padding:20px;">正在加载结果...</div>';
                    document.getElementById('query-results').style.display = 'block';
                    
                    // 发送查询请求
                    fetch(`/api/system_asset_query/{{ system_id }}?${searchParams.toString()}`)
                        .then(response => response.json())
                        .then(data => {
                            displayQueryResults(data);
                        })
                        .catch(error => {
                            resultsContainer.innerHTML = `<div style="color:#e53e3e;padding:15px;">查询失败: ${error.message}</div>`;
                        });
                });
            }
        });
        
        // 加载资产所有者列表
        function loadAssetOwners() {
            fetch(`/api/asset_owners/{{ system_id }}`)
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('asset_owner');
                    // 清除现有选项，保留第一个"所有资产所有者"选项
                    while (select.options.length > 1) {
                        select.remove(1);
                    }
                    
                    // 添加新选项
                    data.forEach(owner => {
                        const option = document.createElement('option');
                        option.value = owner;
                        option.textContent = owner;
                        select.appendChild(option);
                    });
                    
                    // 加载集群名称
                    updateClusterNames();
                })
                .catch(error => console.error('加载资产所有者失败:', error));
        }
        
        // 更新集群名称
        function updateClusterNames() {
            const assetOwner = document.getElementById('asset_owner').value;
            const url = assetOwner 
                ? `/api/cluster_names/{{ system_id }}?asset_owner=${encodeURIComponent(assetOwner)}`
                : `/api/cluster_names/{{ system_id }}`;
                
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('cluster_name');
                    // 清除现有选项，保留第一个"所有集群"选项
                    while (select.options.length > 1) {
                        select.remove(1);
                    }
                    
                    // 添加新选项
                    data.forEach(cluster => {
                        const option = document.createElement('option');
                        option.value = cluster;
                        option.textContent = cluster;
                        select.appendChild(option);
                    });
                })
                .catch(error => console.error('加载集群名称失败:', error));
        }
        
        // 显示查询结果
        function displayQueryResults(data) {
            const resultsContainer = document.getElementById('results-container');
            
            if (data.error) {
                resultsContainer.innerHTML = `
                    <div style="background:#fed7e2;color:#b83280;padding:15px;border-radius:5px;margin-bottom:15px;">
                        <strong>错误：</strong> ${data.error}
                    </div>
                `;
                return;
            }
            
            let html = '';
            
            // 根据查询类型格式化结果
            if (data.query_type === 1) { // 设备数量统计
                html += `
                    <div style="background:#e6fffa;color:#234e52;padding:15px;border-radius:5px;margin-bottom:15px;">
                        <strong>总设备数：</strong> ${data.total_devices || 0}
                    </div>
                    <table style="width:100%;border-collapse:collapse;margin-top:15px;">
                        <thead>
                            <tr>
                                <th style="text-align:left;padding:12px;border-bottom:1px solid #e2e8f0;background:#f7fafc;">集群名称</th>
                                <th style="text-align:left;padding:12px;border-bottom:1px solid #e2e8f0;background:#f7fafc;">设备数量</th>
                                <th style="text-align:left;padding:12px;border-bottom:1px solid #e2e8f0;background:#f7fafc;">资产所有者</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.clusters && data.clusters.length > 0) {
                    data.clusters.forEach(cluster => {
                        html += `
                            <tr>
                                <td style="padding:12px;border-bottom:1px solid #e2e8f0;">${cluster.Cluster_name || '未知'}</td>
                                <td style="padding:12px;border-bottom:1px solid #e2e8f0;">${cluster.Device_count}</td>
                                <td style="padding:12px;border-bottom:1px solid #e2e8f0;">${cluster.Asset_owner || '未知'}</td>
                            </tr>
                        `;
                    });
                } else {
                    html += `<tr><td colspan="3" style="padding:12px;text-align:center;">无数据</td></tr>`;
                }
                
                html += '</tbody></table>';
            } else {
                // 其他查询类型，显示为JSON格式
                html += `
                    <pre style="background:#f7fafc;padding:15px;border-radius:5px;overflow:auto;font-family:monospace;">
${JSON.stringify(data, null, 2)}
                    </pre>
                `;
            }
            
            resultsContainer.innerHTML = html;
        }
        
        // 下载YAML数据
        function downloadYamlData() {
            // 创建一个Blob对象
            const dataStr = JSON.stringify(yamlData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            
            // 创建一个下载链接
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{{ system.name }}_data.json';
            
            // 添加到文档并触发点击
            document.body.appendChild(a);
            a.click();
            
            // 清理
            setTimeout(function() {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 0);
        }
    </script>
</body>
</html>