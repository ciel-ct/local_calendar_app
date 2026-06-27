<template>
  <div class="calendar-app">
    
    <div class="fixed-weekdays-grid">
      <div v-for="day in weekLabels" :key="day" class="weekday-label">{{ day }}</div>
    </div>

    <div class="calendar-scroll-container">
      
      <div v-for="monthGroup in calendarData" :key="monthGroup.monthLabel" class="month-section">
        
        <div class="month-header">
          <h2>{{ monthGroup.monthLabel }} </h2>
        </div>

        <div class="month-grid">
          <div v-for="(week, wIndex) in monthGroup.weeks" :key="wIndex" class="week-row">
            
            <div 
              v-for="(day, dIndex) in week" 
              :key="dIndex" 
              class="day-cell"
              :class="{ 'is-today': day?.isToday, 'is-blank': !day }"
            >
              <template v-if="day">
                <div class="day-number">{{ day.dayNumber }}</div>
                <div class="holiday-name">{{ day.holiday }}</div>
                <div class="day-events">
                  <div v-for="event in day.events" :key="event.id" class="event-bar">
                    {{ event.title }}
                  </div>
                </div>
              </template>
              
              <template v-else>
                <div class="blank-space"></div>
              </template>

            </div>
          </div>
        </div>

      </div>
    </div>

    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const weekLabels = ['日', '月', '火', '水', '木', '金', '土'];
const calendarData = ref([]);
  let timerId = null;

// --- 📅 自分のPythonバックエンドから予定を取ってくる関数 ---
const fetchGoogleCalendarEvents = async (startDate, endDate) => {
  // 💡 向き先をローカルのPythonサーバーに変更！APIキーやカレンダーIDをブラウザに晒さなくて良くなりました 🔒
  const url = `http://localhost:8000/api/events?start=${startDate.toISOString()}&end=${endDate.toISOString()}`;

  try {
    const response = await fetch(url);
    const result = await response.json();
    
    if (result.status === 'success') {
      return result.data; // Pythonが綺麗に取ってきてくれたデータをそのまま使うよっ 🎁
    }
    console.error('Python側でエラーが出たみたい 😢', result.message);
    return [];
  } catch (error) {
    console.error('バックエンドとの通信に失敗しちゃいました 😭', error);
    return [];
  }
};

// --- 📅 カレンダーの生成 ＆ 予定の埋め込みロジック ---
const generateComplexCalendar = async () => {
  const months = [];
  const today = new Date();
  
  // 今週の日曜日（カレンダーの開始日）
  const startDate = new Date();
  startDate.setDate(today.getDate() - today.getDay());
  startDate.setHours(0, 0, 0, 0);

  // 4週間後（カレンダーの終了日）
  const endDate = new Date(startDate);
  endDate.setDate(startDate.getDate() + 28);
  endDate.setHours(23, 59, 59, 999);

  // 1. まずは本物のGoogleカレンダーから予定をドバッと取得！
  const googleEvents = await fetchGoogleCalendarEvents(startDate, endDate);
  const currentCursor = new Date(startDate);

  let currentMonthGroup = null;
  let currentWeek = [];

  // 2. 合計4週間分（28日）ループを回す
  for (let i = 0; i < 28; i++) {

    // Intlを使って、日本時間の「YYYY-MM-DD」を確実に作ります
    const formatter = new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: 'Asia/Tokyo'
    });

    const loopDate = new Date(currentCursor.getTime()); 
    loopDate.setHours(9, 0, 0, 0);
    const year = loopDate.getFullYear();
    const month = loopDate.getMonth() + 1;
    const label = `${loopDate.getFullYear()}年 ${loopDate.getMonth() + 1}月`;
    const dayOfWeek = loopDate.getDay(); // 0:日〜6:土
    // const dateString = loopDate.toISOString().split('T')[0];
    const dateString = formatter.format(loopDate).replace(/\//g, '-');

    // 1. 新しい月に入った、または最初のループの場合の処理
    if (!currentMonthGroup || currentMonthGroup.monthLabel !== label) {
      
      // 前の月グループが残っていれば、作りかけの週を処理して保存
      if (currentMonthGroup) {
        // 週の途中で月が変わった場合、残りの曜日をブランク（null）で埋める
        while (currentWeek.length < 7) currentWeek.push(null);
        currentMonthGroup.weeks.push(currentWeek);
      }

      // 新しい月グループを作成
      currentMonthGroup = { monthLabel: label, weeks: [] };
      months.push(currentMonthGroup);
      
      // 新しい月の最初の週をスタート
      currentWeek = [];
      // 💡 月の最初が日曜日じゃない場合、前側をブランク（null）で埋める
      for (let b = 0; b < dayOfWeek; b++) {
        currentWeek.push(null);
      }
    }
    
    // 3. Googleの予定の中から「今日の日付」に一致するものをフィルターする！
    // 🌟 祝日（holidays）と普通の予定（myEvents）に仕分けます
    let dayHolidayName = null;
    const dayEvents = googleEvents
      .filter(event => {
        // 予定の開始日（終日予定の場合は date、時間指定の場合は dateTime に入るよ 💡）
        const eventStart = event.start.dateTime || event.start.date;
        if (!eventStart) return false;

        // Googleから届いた "2026-07-01T01:00:00Z" から、直接「日本時間の日付文字列」を作っちゃいます！
        const eventDate = new Date(eventStart);
        const eventDateString = formatter.format(eventDate).replace(/\//g, '-');

        // 💡 変換した「日本時間の日付（2026-07-01）」と、マスの「dateString」を比べる！
        return eventDateString === dateString;

      })
      .map(event => ({
        id: event.id,
        title: event.summary // Googleの予定のタイトルは「summary」っていう名前なんですっ
      }));

    // 日付データを追加
    currentWeek.push({
      dayNumber: loopDate.getDate(),
      isToday: dateString === formatter.format(today).replace(/\//g, '-'),
      holiday: dayHolidayName,
      events: dayEvents // 🌟 本物の予定がここに入る！
    });

    // 3. 土曜日（週の終わり）まで来たら、週を月グループにプッシュして新しい週を作る
    if (currentWeek.length === 7) {
      currentMonthGroup.weeks.push(currentWeek);
      currentWeek = [];
    }

    // 次の日に進める
    currentCursor.setDate(currentCursor.getDate() + 1);
  }

  // 最後に残った週があればプッシュ
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) currentWeek.push(null);
    currentMonthGroup.weeks.push(currentWeek);
  }

  calendarData.value = months;
};

// --- 🚀 画面が立ち上がった時の処理（ライフサイクル） ---
onMounted(() => {
  // 1. 最初の一回を実行
  generateComplexCalendar();

  // 3分（180,000ミリ秒）ごとに、上の関数を自動で呼び出します
  timerId = setInterval(generateComplexCalendar, 180000);
});

// --- 🛑 画面が閉じられた時のクリーンアップ ---
onUnmounted(() => {
  // メモリリークを防ぐためにタイマーを止めます
  if (timerId) clearInterval(timerId);
});
</script>

<style scoped>
/* --- 📱 全体のスタイル --- */
.calendar-app {
  width: 100vw;
  height: 100vh;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background-color: #fafafa;
  box-sizing: border-box;
  overflow: hidden;
  
  /* 曜日ヘッダーとスクロールエリアを縦に並べる */
  display: flex;
  flex-direction: column;
}

/* 🌟 新設：一番上にずっと固定される曜日ヘッダー */
.fixed-weekdays-grid {
  flex-shrink: 0; /* 縦に縮まないように固定 */
  display: grid;
  grid-template-columns: repeat(7, 1fr); /* 下のカレンダーのマスと完全に幅を合わせる */
  text-align: center;
  font-weight: bold;
  background-color: #fff; /* 背景を白にして下の文字が透けないように */
  border-bottom: 2px solid #ffb6c1; /* しえるちゃんピンクの可愛い区切り線 */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
  z-index: 10; /* カレンダーのマスより必ず上に表示するお守り */
}

.weekday-label {
  color: #5f6368;
  font-size: 14px;
}
.weekday-label:nth-child(1) { color: #ffffff; background-color: #ff93b7;} /* 日曜日 */
.weekday-label:nth-child(7) { color: #ffffff; background-color: #56a8ff;} /* 土曜日 */

/* 縦にスクロールできるコンテナ */
/* .calendar-scroll-container {
  flex-grow: 1; 
  overflow-y: auto;
  padding: 15px;
  box-sizing: border-box;
} */

/* 月ごとのセクション */
.month-section {
  background: white;
  border-radius: 16px;
  /* padding: 0 0 0 15px; */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
}

/* 月ヘッダー */
.month-header h2 {
  color: #ff6699;
  margin: 0 0 0 0;
  font-size: 22px;
  border-left: 5px solid #ff6699;
  padding-left: 10px;
}

/* カレンダーメイン格子 */
.month-grid {
  border-top: 1px solid #9d9d9d;
}

.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.day-cell {
  border-right: 1px solid #9d9d9d;
  border-bottom: 1px solid #9d9d9d;
  padding: 3px 0 0 0;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  height: clamp(85px, 17vh, 200px);
  min-width: 0;
}

.is-blank {
  background-color: #d7d7d7;
}

.day-number {
  font-size: 20px;
  font-weight: 500;
  color: #3c4043;
  text-align: center;
  /* width: 20px;
  height: 20px; */
  line-height: 20px;
  margin: 0 auto 0 auto;
}

.is-today {
  background-color: #eecaf9;
}
.is-today .day-number {
  background-color: #ff6699;
  color: #fff;
  border-radius: 25%;
}

/*祝日の文字デザイン（日付の下に小さく可愛く） */
.holiday-name {
  font-size: 10px;
  color: #ff4d79; /* ちょっと濃いめの可愛いピンク */
  text-align: center;
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 0 2px;
}

/* 予定のバー */
.day-events {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}
.event-bar {
  background-color: #ffe6e6;
  color: #ff3377;
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 3px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  font-weight: bold;
}
/* 🌸 祝日の文字デザイン（日付の下に小さく可愛く） */
.holiday-name {
  font-size: 10px;
  color: #ff4d79; /* ちょっと濃いめの可愛いピンク */
  text-align: center;
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 0 2px;
}
</style>