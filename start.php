php
<?php
echo "<h2>🤖 Запуск Telegram бота</h2>";

// Проверяем доступ к Python
echo "<p>Проверяем Python...</p>";

// Пробуем выполнить простую команду
$test = shell_exec("python3 --version 2>&1");
echo "<p>Версия Python: $test</p>";

// Запускаем бота
echo "<p>Запускаю бота...</p>";
$command = "cd " . __DIR__ . " && python3 bot.py > bot.log 2>&1 &";
$result = shell_exec($command);

if ($result === null) {
    echo "<p style='color: green; font-weight: bold;'>✅ Бот запущен в фоне!</p>";
} else {
    echo "<p style='color: green;'>✅ Команда выполнена</p>";
}

echo "<hr>";
echo "<p><a href='./bot.py'>Посмотреть код бота</a></p>";
echo "<p><a href='./bot.log'>Посмотреть лог (если есть)</a></p>";
echo "<p><a href='../'>На главную сайта</a></p>";
?>
