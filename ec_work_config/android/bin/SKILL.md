---
name: ec-android-cli
description: >-
  中文：EasyClick ec-android-cli 的安装前提、子命令、参数与示例；以及 EasyClick Android 自动化（EC 脚本、选择器、图色、OCR、UI 等）的 API 速查与开发规范。
  English: For ec-android-cli usage and EasyClick automation (EC scripts, UI, nodes, OCR); invoke when user asks about CLI, EC APIs, or EasyClick development.
---

# ec-android-cli 使用说明

## 使用前提

- 本机已启动 **IntelliJ IDEA**，并已加载 **EasyClick 开发工具**插件；插件需处于可响应命令的状态。
- 命令行中的 **模块名** 与 IDEA 里该脚本工程对应的 **模块名** 一致。
- 多窗口、多工程时，建议用 **`-p`** 传入与 IDEA 中打开路径一致的 **工程根目录**，便于匹配到正确实例。

## 程序名与帮助

- **本仓库自带可执行文件**（相对仓库根目录）：**`ec_work_config/android/bin/ec-android-cli`**
  - 在仓库根下：`./ec_work_config/android/bin/ec-android-cli -h`
  - Agent / 脚本优先使用该路径，避免依赖全局 PATH。
  - 并且输出的日志格式设置为json格式
- 若本机已单独安装并加入 PATH，也可直接执行 **`ec-android-cli`**（与上述为同一程序；本地若改名，请将命令中的名称一并替换）。
- 查看总帮助：`./ec_work_config/android/bin/ec-android-cli -h`（或在 PATH 已配置时：`ec-android-cli -h`）
- 查看子命令帮助：`./ec_work_config/android/bin/ec-android-cli <子命令> -h`

## 子命令一览

| 子命令 | 作用 |
|--------|------|
| `preview` | 预览工程 |
| `run` | 运行工程 |
| `stop` | 停止当前运行 |
| `build` | 构建 IEC |
| `capture-screen` | 截图（从 IDEA 已连接设备抓取截图并返回路径） |
| `capture-node` | 抓取 UI 节点（UIX，本质为 XML）并返回路径 |
| `refresh-node` | 刷新当前设备 UI 节点树 |
| `set-node-params` | 设置调试节点抓取参数并同步到手机 |
| `ocr-local-image` | OCR 识别本地图像并输出识别结果 |
| `ocr-screen` | OCR 识别当前屏幕并输出识别结果 |
| `test-image` | 图片模板匹配测试（本图/抓屏）并输出测试结果 |
| `monitor` | 仅持续输出日志流（不要求 `-m`） |

**说明：** 除 `monitor` 外，其余子命令均需 **`-m`（模块名）**；`monitor` 不需要模块名。

## 通用参数（除 `monitor` 外的大多数子命令）

| 参数 | 含义 |
|------|------|
| **`-m` / `--module`** | **必填**。IDEA 模块名。 |
| **`-p` / `--project`** | 可选。工程根目录路径（与 IDEA 中打开路径一致）。 |
| **`-f` / `--format`** | 可选。日志行格式：`text` 或 `json`；**省略时默认为 `json`**。 |
| **`-o` / `--log`** | 可选。将日志**追加**写入指定文件路径。 |
| **`-k` / `--stop-on`** | 可选。日志中**包含**该子串时，打印提示并**退出**（结束本次日志监控）。多个条件为**或**关系时，可用 **`|||`** 连接多个子串（任一子串命中即退出）。 |
| **`-w` / `--monitor-logs`** | 可选。`true` / `false`。**`preview` / `run` / `stop`**：未写 `-w` 时视为 **`true`**（持续跟日志至 **Ctrl+C** 或命中 `-k`）。**`build`**：未写 `-w` 时为 **`false`**（操作结束后即结束日志）。显式写 `-w true` / `-w false` 可覆盖。 |
| **`-r` / `--random-log`** | 可选。`true` / `false`。为 `true` 时在 **`ai_logs/`** 下自动生成日志文件名；**不可与 `-o` 同时使用**。 |

**约束：** 凡写出的可选参数须带**有效取值**；**`-r` 与 `-o` 不能同时使用**。

**`-k` 多关键字（通用）：** 所有支持 **`-k`** 的子命令——**`preview` / `run` / `stop` / `build` / `monitor`**——均可用 **`|||`** 连接多个子串，表示**或**：日志中**任一**子串出现即结束本次监控。

**`preview` 专用：** 未写 **`-k` / `--stop-on`** 时，默认停止关键字为 **`执行UI结束`**；未写 **`-w`** 时默认**持续监控日志**（等同 `-w true`）。
- **`-P` / `--param key=value`**：可多次。值类型：`true`/`false`/`yes`/`no`/`1`/`0` → 布尔；整数 → 数字；**小数/科学计数（如 `1.5`、`-2e-3`）→ 浮点数**；否则字符串。脚本中使用getCliArgs()函数获取。

**`run` 专用：** 未写 **`-k`** 时，默认停止关键字为 **`脚本已运行结束`**；未写 **`-w`** 时默认**持续监控日志**（等同 `-w true`）。
- **`-P` / `--param key=value`**：可多次。值类型：`true`/`false`/`yes`/`no`/`1`/`0` → 布尔；整数 → 数字；**小数/科学计数（如 `1.5`、`-2e-3`）→ 浮点数**；否则字符串。脚本中使用getCliArgs()函数获取。


**`stop` 专用：** 未写 **`-k`** 时，默认在日志中出现 **`停止失败`**、**`停止运行成功`** 或 **`无设备连接`** 时结束监控（**任一**命中即可）；未写 **`-w`** 时默认**持续监控日志**（等同 `-w true`）。若显式传入 **`-k`**，则以你设置的关键字为准（仍可用 **`|||`** 表示多关键字“或”）。

**`build`（编译 IEC）专用：** 未写 **`-k`** 时，默认在日志中出现 **`release.iec`**、**`编译IEC成功`** 或 **`编译失败`** 时结束本次日志监控（**任一**命中即可）。

## `monitor` 专用参数

仅日志流；不使用 `-m`、`-p`、`-w`。

| 参数 | 含义 |
|------|------|
| **`-f` / `--format`** | 同上文，`text` 或 `json`，默认 `json`。 |
| **`-o` / `--log`** | 同上文。 |
| **`-k` / `--stop-on`** | 同上文。 |
| **`-r` / `--random-log`** | 同上文（勿与 `-o` 同用）。 |

## 日志输出习惯

- 常规日志多输出到 **标准错误（stderr）**；使用 **`-o`** 或 **`-r`** 时还会写入文件。
- 默认日志行格式为 **JSON**，除非指定 **`-f text`**。

## 示例

```bash
# 以下假定当前目录为仓库根；`EC` 即 ./ec_work_config/android/bin/ec-android-cli
EC=./ec_work_config/android/bin/ec-android-cli
$EC preview -m app -P a=1
$EC preview -m app -f json
$EC run -m app -f json -o /tmp/easyclick.log
$EC run -m app -r true -P a=1
$EC run -m app -w false
$EC stop -m app
$EC build -m app
$EC capture-screen -m app
$EC capture-node -m app -d /tmp/nodes
$EC refresh-node -m app
$EC set-node-params -m app -M 1
$EC ocr-local-image -m app -i /tmp/a.png
$EC ocr-screen -m app
$EC test-image -m app -s /tmp/s.png
$EC monitor
$EC monitor -f text -o /tmp/monitor.log -k "完成"
```

多工程时示例：

```bash
./ec_work_config/android/bin/ec-android-cli run -m app -p /path/to/project/root
```

## `capture-screen`（截图）

- **用途**：调用截图，成功后会输出路径。
- **常用短参数**：
  - `-n`：`--only-network`
  - `-d`：`--dir`

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC capture-screen -m app
$EC capture-screen -m app -n -d /tmp/shots
```

## `capture-node`（抓取节点 UIX）

- **用途**：调用抓节点功功能，成功后在 输出 uix文件路径。
- **常用短参数**：
  - `-d`：`--dir`

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC capture-node -m app
$EC capture-node -m app -d /tmp/nodes
```

## `refresh-node`（刷新节点）

- **用途**：刷新当前已连接设备的 UI 节点树。
- **默认 `-k`**：`刷新节点结果|||请先连接设备`

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC refresh-node -m app
```

## `set-node-params`（设置节点参数）

- **用途**：设置调试节点抓取参数并同步到手机（与 IDEA「调试节点设置」一致，不经对话框）。
- **可选短参数**（未传则保留设备当前值）：
  - `-M` / `--mode`：节点模式 `1|2|增强型|快速型`
  - `-a` / `--algorithm`：`nsf|bsf|dsf`
  - `-i` / `--fetch-invisible`：隐藏元素 `true|false|是|否`
  - `-N` / `--fetch-not-important`：不重要元素 `true|false|是|否`
- **HTTP 短名字段**：仅发送已指定的 `m`、`a`、`fin`、`fni`（插件亦接受长名 `mode`、`algorithm` 等）
- **默认 `-k`**：`调试节点设置成功|||调试节点设置失败|||请先连接设备`

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC set-node-params -m app -M 1
$EC set-node-params -m app -a nsf -i true
$EC set-node-params -m app --mode 增强型 --algorithm bsf --fetch-invisible 是 --fetch-not-important 否
```

## `ocr-local-image`（OCR 本地图像）

- **用途**：调用 成功后输出 OCR 结果字符串。
- **必填**：`-i/--path` 本地图像路径
- **可选**：
  - `-t/--ocr-type`：`paddleOcrNcnnV5|paddleOcrOnnxV4|paddleOcrOnnxV5|ocrLite`（默认 `paddleOcrNcnnV5`）
  - `-P/--padding`：默认 `32`
  - `-X/--max-side-len`：默认 `640`
  - `-R/--release`：默认 `false`

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC ocr-local-image -m app -i /path/to/image.png
$EC ocr-local-image -m app -i a.jpg -t paddleOcrOnnxV5 -P 48 -X 960 -R
```

## `ocr-screen`（OCR 屏幕）

- **用途**：调用成功后在OCR 结果字符串。
- **可选**（同 `ocr-local-image`，但不需要 `--path`）：
  - `-t/--ocr-type`（默认 `paddleOcrNcnnV5`）
  - `-P/--padding`（默认 `32`）
  - `-X/--max-side-len`（默认 `640`）
  - `-R/--release`（默认 `false`）

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC ocr-screen -m app
$EC ocr-screen -m app -t paddleOcrOnnxV5 -P 48 -X 960 -R
```

## `test-image`（图片测试）

- **用途**：调用成功后在 测试结果字符串。
- **必填**：`-s/--small-image-path` 小图路径
- **可选**（均为字符串格式）：
  - `-T/--test-type`：`1` 本图测试；`2` 抓屏测试（默认 `2`）。`test-type=2` 时无需 `--big-image-path`
  - `-B/--big-image-path`：大图路径（仅 `test-type=1` 时需要）
  - `-F/--func`：`findImageByColor|findImage|matchTemplate`（默认 `findImage`）
  - `-M/--method`：模板匹配方式（默认 `5`）
  - `-g/--range`：默认 `0,0,0,0`
  - `-l/--limit`：默认 `1`
  - `-L/--max-level`：默认 `-1`
  - `-E/--weak-threshold`：默认 `0.7`
  - `-H/--threshold`：默认 `0.8`
  - `-C/--opencv-mat`：`1` 否；`2` 是（默认 `1`）

```bash
EC=./ec_work_config/android/bin/ec-android-cli
$EC test-image -m app -s /tmp/s.png
$EC test-image -m app -T 1 -s s.png -B b.png -F matchTemplate -M 5
$EC test-image -m app -F findImage -g 0,0,0,0 -l 1 -E 0.7 -H 0.8
```

---

# EasyClick 开发专家（EC 脚本与 API 速查）


EasyClick是Android自动化测试和脚本开发工具，支持无障碍、代理、蓝牙HID、OTG HID四种运行模式。

**运行模式说明：**
- **无障碍模式**：使用系统无障碍服务，可使用全部功能
- **代理模式**：连接电脑或代理服务，可使用全部功能
- **蓝牙HID模式**：通过蓝牙HID设备操作，只能用图色/OCR/蓝牙点击滑动
- **OTG HID模式**：通过OTG HID设备操作，只能用图色/OCR/OTG点击滑动

**功能查询规范：**
- 所有API功能可在项目`libs`目录下的对应js文件中查询
- 基础函数查看`basic.js`，图像处理查看`image.js`，OCR相关查看`image.js`中的ocr部分
- **节点信息**相关功能查看`nodeimage`目录
- **截屏信息**相关功能查看`clorimage`目录
- **CLI命令行工具**功能见**本文档第一节**《ec-android-cli 使用说明》（仓库内源码为 `cli_ai`）
- 建议阅读文件头部的函数注释了解详细用法和参数说明

---
## 一、核心模块
### 1.1 基础函数
```javascript
logd(msg)/logi(msg)/logw(msg)/loge(msg)   // 日志输出（蓝/绿/黄/红）
toast(msg)                                // Toast提示
sleep(ms)                                 // 休眠（毫秒）
exit()                                    // 退出脚本
startEnv()                                // 启动无障碍服务
isServiceOk()                             // 检查服务是否正常
```
### 1.2 选择器
```javascript
text(str)/textMatch(reg)                  // 文本包含/正则
textStartsWith(str)/textEndsWith(str)     // 文本开头/结尾
desc(str)/descMatch(reg)                  // 描述包含/正则
id(str)/idMatch(reg)                      // ID包含/正则
clz(str)/clzMatch(reg)                    // 类名包含/正则
pkg(str)/pkgMatch(reg)                    // 包名包含/正则
bounds(l,t,r,b)                           // 边界范围
selector.and(s2)/selector.or(s2)          // 与/或条件
```
### 1.3 节点操作
```javascript
// 获取节点
selector.getOneNodeInfo(timeout)          // 获取单个节点
selector.getNodeInfo(timeout)             // 获取所有匹配节点
selector.has()                            // 判断是否存在
selector.waitExistNode(timeout)           // 等待节点出现
// 节点属性
node.text/node.desc/node.id/node.clz/node.pkg     // 文本/描述/ID/类名/包名
node.bounds                               // 边界{l,t,r,b}
node.clickable/node.visible/node.childCount       // 是否可点击/可见/子节点数
// 节点操作
node.click()/node.longClick()             // 点击/长按
node.inputText(content)/node.clearText()  // 输入/清空文本
node.scrollForward()/node.scrollBackward()// 向前/后滚动
node.parent()/node.child(index)           // 获取父/子节点
```
### 1.4 全局操作
```javascript
clickPoint(x,y)/longClickPoint(x,y)/doubleClickPoint(x,y)   // 点击/长按/双击
swipeToPoint(x1,y1,x2,y2,duration)        // 滑动到指定坐标
swipeUp()/swipeDown()/swipeLeft()/swipeRight()              // 上/下/左/右滑
touchDown(x,y)/touchMove(x,y)/touchUp(x,y)// 触摸控制
inputText(selectors,content)              // 输入文本
clearTextField(selectors)                 // 清空文本
getOneNodeInfo(selectors,timeout)         // 获取单个节点
has(selectors)/waitExistNode(selectors,timeout) // 判断/等待节点
dumpXml()                                 // 获取节点XML
```
### 1.5 设备信息
```javascript
device.getScreenWidth()/getScreenHeight() // 屏幕宽高
device.getIMEI()/getBrand()/getModel()    // IMEI/品牌/机型
device.getAndroidId()/getMacAddress()     // Android ID/MAC
device.getBrightness()/setBrightness(b)   // 获取/设置亮度
device.getBattery()                       // 电量
device.vibrate(millis)                    // 震动
```
### 1.6 工具函数
```javascript
utils.openApp(packageName)                // 打开应用
utils.openAppByName(appName)              // 通过名称打开
utils.isAppExist(packageName)             // 判断是否已安装
utils.getAppVersionCode(packageName)      // 获取版本号
utils.showLogWindow()/hideLogWindow()     // 显示/隐藏日志窗
```
---
## 二、图像处理
```javascript
image.requestScreenCapture(timeout,type)  // 请求截图权限
image.captureScreen()                     // 截图
image.captureToFile(retry,x,y,ex,ey,path) // 截图到文件
image.readImage(path)/saveImage(img,path) // 读取/保存图片
image.findImageEx(template,x,y,ex,ey,weakThresh,thresh,limit,method)  // 找图
image.findColorEx(color,thresh,x,y,ex,ey,limit,orz)                   // 找色
image.findMultiColorEx(firstColor,points,thresh,x,y,ex,ey,limit,orz)  // 多点找色
img.getWidth()/getHeight()                // 获取宽高
img.pixel(x,y)                            // 获取像素颜色
img.recycle()                             // 回收图像
```
---
## 三、OCR识别
```javascript
let ocrInst=ocr.newOcr()
ocrInst.initOcr({"type":"paddleOcrNcnnV5","numThread":2,"padding":32,"maxSideLen":640})
let results=ocrInst.ocrImage(img,timeout,map)  // 返回[{label,confidence,x,y,width,height}]
ocrInst.ocrFile(path,timeout,map)           // 识别图片文件
ocrInst.releaseAll()                        // 释放资源
```
---
## 四、文件操作
```javascript
file.readFile(path)/writeFile(data,path)  // 读取/写入
file.copyFile(src,dest)/moveFile(src,dest)// 复制/移动
file.deleteFile(path)                     // 删除
file.exists(path)/isFile(path)/isDir(path)// 判断存在/文件/目录
file.create(path)/listDir(path)           // 创建/列出目录
```
---
## 五、网络请求
```javascript
http.httpGetDefault(url,timeout,headers)  // GET请求
http.httpPost(url,params,files,timeout,headers)  // POST请求
http.postJSON(url,json,timeout,headers)   // POST JSON
http.downloadFile(remoteUrl,file,timeout,headers)  // 下载文件
```
---
## 六、数据库
```javascript
sqlite.connectOrCreateDb(dbName)          // 连接/创建数据库
sqlite.createTable(tableName,columns)     // 创建表
sqlite.insert(tableName,map)              // 插入数据
sqlite.update(tableName,map,where)        // 更新数据
sqlite.query(sql)/execSql(sql)            // 查询/执行SQL
sqlite.close()                            // 关闭数据库
```
---
## 七、多线程
```javascript
thread.execAsync(runnable)                // 异步执行，返回线程ID
thread.cancelThread(threadId)/stopAll()   // 取消线程/全部
setTimeout(func,timeout)                  // 延迟执行
setInterval(func,interval)                // 周期执行
```
---
## 八、UI界面
```javascript
ui.layout(name,content)                   // 加载XML布局
ui.findViewById(id)                       // 通过ID查找视图
ui.setVisibility(view,visibility)         // 设置可见性
ui.setText(view,text)/getText(view)       // 设置/获取文本
ui.setEvent(view,eventType,callback)      // 设置事件监听
ui.putShareData(key,value)/getShareData(key)  // 存储/获取共享数据
ui.customDialog(params,view,bind,dismiss) // 自定义对话框
```
---
## 九、Shell命令
```javascript
shell.installApp(path)                    // 安装APK
shell.uninstallApp(packageName)           // 卸载应用
shell.stopApp(packageName)                // 停止应用
shell.execCommand(command)                // 执行Shell命令
shell.sudo(command)                       // 执行Root命令
```
---
## 十、HID模块
```javascript
// 蓝牙HID
bleEvent.startConnect(name,save,timeout)  // 连接蓝牙设备
bleEvent.isConnected()                    // 是否已连接
bleEvent.clickPoint(x,y)/swipe(x0,y0,x1,y1,duration)  // 点击/滑动
bleEvent.home()/back()                    // 主页/返回键
// OTG HID
otgEvent.init()/connectFirst()            // 初始化/连接
otgEvent.isConnected()                    // 是否已连接
otgEvent.clickPoint(x,y)/swipe(x0,y0,x1,y1,duration)  // 点击/滑动
```
---
## 十一、对象扩展
```javascript
// Point对象
point.click()/longClick()/doubleClick()   // 点击/长按/双击
// Rect对象
rect.click()/clickRandom()                // 点击中心/随机位置
// String扩展
str.contains(s)/replaceAll(s1,s2)/trim()/toInt()  // 包含/替换/去空格/转整数
```
---
## 十二、代码模板
```javascript
// 启动环境
function main(){if(!autoServiceStart(3)){loge("服务启动失败");return;}}
function autoServiceStart(time){for(let i=0;i<time;i++){if(isServiceOk())return true;startEnv();sleep(1000);}return isServiceOk();}
main();
// 查找点击
let node=text("推荐").getOneNodeInfo(0);if(node)node.click();else loge("未找到");
// 滑动
let w=device.getScreenWidth(),h=device.getScreenHeight();swipeToPoint(w/2,h*0.8,w/2,h*0.2,500);
// OCR
let ocrInst=ocr.newOcr();ocrInst.initOcr({"type":"paddleOcrNcnnV5","numThread":2,"padding":32,"maxSideLen":640});let img=image.captureScreen();let results=ocrInst.ocrImage(img,5000,null);if(results)for(let i=0;i<results.length;i++)logd(results[i].label);ocrInst.releaseAll();
```
