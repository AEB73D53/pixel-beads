/*
 * 拼豆助手 · WS2812 拼豆板 —— Arduino UNO 串口「LED 反馈」验证固件
 *
 * 目的：不靠串口监视器，用板载 L 灯（13 脚）的亮灭来确认「PC exe → 串口 → 板子」链路是否通。
 *
 * 行为：
 *   - 收到一帧完整、校验通过的协议帧  → 板载 L 灯快速闪 3 下（= 链路 OK）
 *   - 收到帧但校验失败 / 尺寸非法     → L 灯常亮 1 秒后熄灭（= 数据不对）
 *   - 完全没收到任何数据              → L 灯无反应
 *
 * 用法：
 *   1. 烧录本固件，串口监视器波特率设 115200。
 *   2. 完全退出 Arduino（释放 COM3）。
 *   3. 在 PC exe「导出拼豆板」里点「测试灯板」（或发送图纸），波特率 115200。
 *   4. 看板载 L 灯：闪 3 下 = 数据正确送达。
 *
 * 协议（与 serial_out.py 一致）：
 *   帧头 0xAA 0x55 | 行(1B) | 列(1B) | rows×cols×3(每颗 GRB) | 校验和(1B) | 帧尾 0x0D 0x0A
 *
 * 说明：UNO 内存只有 2KB，29×29 整帧装不下，故这里只校验协议与校验和，
 *       不缓存整帧。真正点亮 29×29 灯板请用 STM32F411 固件。
 */

#define FRAME_HEAD0 0xAA
#define FRAME_HEAD1 0x55
#define FRAME_TAIL0 0x0D
#define FRAME_TAIL1 0x0A

// ---------- 收帧状态机 ----------
enum { ST_IDLE, ST_H1, ST_ROWS, ST_COLS, ST_DATA, ST_CSUM, ST_TAIL0, ST_TAIL1 };
uint8_t st = ST_IDLE;
uint8_t rows = 0, cols = 0;
uint32_t dataLen = 0;      // 数据区应有多少字节
uint32_t gotData = 0;      // 实际收到多少数据字节
uint8_t calcCsum = 0;      // 边收边累加校验和
uint8_t recvCsum = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(115200);
  while (!Serial) { ; }
  Serial.println("=== 拼豆板串口固件就绪(115200)：收到合法帧会闪 L 灯 3 下 ===");
}

void loop() {
  while (Serial.available() > 0) {
    handleByte((uint8_t)Serial.read());
  }
}

void handleByte(uint8_t b) {
  switch (st) {
    case ST_IDLE:
      if (b == FRAME_HEAD0) st = ST_H1;
      break;
    case ST_H1:
      if (b == FRAME_HEAD1) st = ST_ROWS;
      else if (b != FRAME_HEAD0) st = ST_IDLE;
      break;
    case ST_ROWS:
      rows = b; st = ST_COLS; break;
    case ST_COLS:
      cols = b;
      dataLen = (uint32_t)rows * cols * 3;
      gotData = 0; calcCsum = 0;
      if (dataLen == 0 || dataLen > 5000) {
        badFrame();      // 非法尺寸
        st = ST_IDLE;
      } else {
        st = ST_DATA;
      }
      break;
    case ST_DATA:
      calcCsum += b;      // 累加校验和
      gotData++;
      if (gotData >= dataLen) st = ST_CSUM;
      break;
    case ST_CSUM:
      recvCsum = b; st = ST_TAIL0; break;
    case ST_TAIL0:
      if (b == FRAME_TAIL0) st = ST_TAIL1; else { badFrame(); st = ST_IDLE; }
      break;
    case ST_TAIL1:
      if (b == FRAME_TAIL1) {
        if (recvCsum == calcCsum) goodFrame();
        else badFrame();
      } else {
        badFrame();
      }
      st = ST_IDLE;
      break;
  }
}

// 收到合法帧 → L 灯快速闪 5 次（节奏明显区别于板子常亮的电源灯，一眼可辨）
void goodFrame() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(150);
    digitalWrite(LED_BUILTIN, LOW);
    delay(150);
  }
}

// 收到帧但数据不对 → L 灯常亮 1 秒
void badFrame() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
}
