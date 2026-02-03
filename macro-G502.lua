--FPS压枪宏 v2.0  Camvanaa @2026
--支持多枪械配置、按子弹弹道配置、射速计算、垂直/水平倍率

--====================================================================================
-- 基础配置
--====================================================================================
local scriptName = "MountCloud_SCRIPT"
local showLog = true                    -- 是否打印日志
local clickBtn = 1                      -- 触发按键 (左键=1)

-- 按键配置
local toggleBtn = 6                     -- 压枪开关 (G6键) - 按一次开启，再按一次关闭
local gunSwitchUpBtn = 8                -- 切换下一把枪 (DPI+)
local gunSwitchDnBtn = 7                -- 切换上一把枪 (DPI-)
local resetPointBtn = 5                 -- 鼠标复位开关 (前进键)
local resetConfigBtn = 9                -- 配置复位 (G9键)

--====================================================================================
-- 枪械配置
-- rpm: 每分钟射速
-- verticalMul: 垂直倍率 (值越大压枪越强)
-- horizontalMul: 水平倍率 (值越大左右补偿越强)
-- pattern: 弹道配置，每个元素对应一发子弹 {y=垂直后坐力, x=水平后坐力}
--          x正值=向右, x负值=向左
--          y正值=向下(需要向下补偿), 一般都是正值
--====================================================================================
local guns = {
        -- M14
    {
        name = "TestGun",
        rpm = 727,
        verticalMul = 1.0,
        horizontalMul = 1.0,
        pattern = {
            {y=13, x=0},    -- 第1发
            {y=26, x=-7},    -- 第2发
            {y=24, x=-5},    -- 第3发
            {y=24, x=7},    -- 第4发
            {y=20, x=7},    -- 第5发
            {y=19, x=8},    -- 第6发
            {y=18, x=-5},    -- 第7发
            {y=15, x=-4},    -- 第8发
            {y=15, x=3},    -- 第9发
            {y=13, x=7},    -- 第10发
            {y=13, x=-5},    -- 第11发
            {y=11, x=-6},    -- 第12发
            {y=9, x=-5},    -- 第13发
            {y=8, x=-8},    -- 第14发
            {y=8, x=4},    -- 第15发
            {y=12, x=-5},    -- 第16发
            {y=11, x=-6},    -- 第17发
            {y=8, x=-5},    -- 第18发
            {y=10, x=-5},    -- 第19发
            {y=26, x=-9},    -- 第20发
            {y=6, x=-5},    -- 第21发
            {y=7, x=-4},    -- 第22发
            {y=6, x=-4},    -- 第23发
            {y=6, x=-4},    -- 第24发
            {y=6, x=-4},    -- 第25发
            {y=7, x=-4},    -- 第26发
            {y=6, x=-4},    -- 第27发
            {y=7, x=-4},    -- 第28发
            {y=6, x=-4},    -- 第29发
            {y=6, x=-4},    -- 第30发
        }
    },
}

--====================================================================================
-- 运行时状态 (不要修改)
--====================================================================================
local currentGunIndex = 1               -- 当前选择的枪械索引
local currentBullet = 0                 -- 当前子弹计数
local recoilEnabled = false             -- 压枪开关状态
local resetPointState = false           -- 鼠标复位开关
local totalMoveY = 0                    -- 记录总垂直移动量(用于复位)
local totalMoveX = 0                    -- 记录总水平移动量(用于复位)
local errorY = 0                        -- Y轴小数误差累加
local errorX = 0                        -- X轴小数误差累加

--====================================================================================
-- 辅助函数
--====================================================================================

-- 根据RPM计算每发子弹的间隔时间(毫秒)
function getSleepTime()
    local gun = guns[currentGunIndex]
    return math.floor(60000 / gun.rpm)
end

-- 获取当前枪械
function getCurrentGun()
    return guns[currentGunIndex]
end

-- 获取指定子弹的后坐力数据（返回小数值，不做取整）
function getBulletRecoil(bulletIndex)
    local gun = getCurrentGun()
    local pattern = gun.pattern
    
    -- 如果子弹数超过配置的弹道数据，使用最后一个
    if bulletIndex > #pattern then
        bulletIndex = #pattern
    end
    if bulletIndex < 1 then
        bulletIndex = 1
    end
    
    local recoil = pattern[bulletIndex]
    local moveY = recoil.y * gun.verticalMul
    local moveX = recoil.x * gun.horizontalMul
    
    return moveY, moveX
end

-- 将小数转换为整数移动量，累加误差到下一次
-- 原理：每次移动取整后，把小数部分累加起来，当累加值>=1时补偿
function applyMovement(rawY, rawX)
    -- 加上之前累积的误差
    local totalY = rawY + errorY
    local totalX = rawX + errorX
    
    -- 取整作为实际移动量
    local moveY = math.floor(totalY)
    local moveX = math.floor(totalX)
    
    -- 保存小数误差到下一次
    errorY = totalY - moveY
    errorX = totalX - moveX
    
    return moveY, moveX
end

-- 切换枪械
function switchGun(delta)
    currentGunIndex = currentGunIndex + delta
    if currentGunIndex < 1 then
        currentGunIndex = #guns
    end
    if currentGunIndex > #guns then
        currentGunIndex = 1
    end
    local gun = getCurrentGun()
    log("Switch to gun: %s (RPM=%d, vMul=%.1f, hMul=%.1f)", 
        gun.name, gun.rpm, gun.verticalMul, gun.horizontalMul)
end

-- 日志函数
function log(str, ...)
    if showLog then
        OutputLogMessage(scriptName .. "-[INFO]-" .. str .. "\n", ...)
    end
end

--====================================================================================
-- 核心功能
--====================================================================================

-- 开启左键事件报告
EnablePrimaryMouseButtonEvents(true)

-- 主事件处理
function OnEvent(event, arg)
    log("event=%s,arg=%s", event, arg)
    
    -- 压枪开关 (G6键)
    if event == "MOUSE_BUTTON_PRESSED" and arg == toggleBtn then
        recoilEnabled = not recoilEnabled
        log("Recoil control: %s", recoilEnabled and "ON" or "OFF")
        return
    end
    
    -- 切换枪械 - 下一把
    if event == "MOUSE_BUTTON_PRESSED" and arg == gunSwitchUpBtn then
        switchGun(1)
        return
    end
    
    -- 切换枪械 - 上一把
    if event == "MOUSE_BUTTON_PRESSED" and arg == gunSwitchDnBtn then
        switchGun(-1)
        return
    end
    
    -- 鼠标复位开关
    if event == "MOUSE_BUTTON_PRESSED" and arg == resetPointBtn then
        resetPointState = not resetPointState
        log("Mouse reset: %s", resetPointState and "ON" or "OFF")
        return
    end
    
    -- 配置复位
    if event == "MOUSE_BUTTON_PRESSED" and arg == resetConfigBtn then
        resetConfig()
        return
    end
    
    -- 开始压枪 (压枪开关开启时)
    if event == "MOUSE_BUTTON_PRESSED" and arg == clickBtn and recoilEnabled then
        beginRecoilControl()
    end
end

-- 执行压枪
function beginRecoilControl()
    local gun = getCurrentGun()
    local sleepTime = getSleepTime()
    
    currentBullet = 0
    totalMoveY = 0
    totalMoveX = 0
    errorY = 0  -- 重置误差累加
    errorX = 0
    
    log("Start recoil control: %s, interval=%dms", gun.name, sleepTime)
    
    -- 首发延迟（等待第一发子弹发射）
    Sleep(math.floor(sleepTime / 2))
    
    repeat
        currentBullet = currentBullet + 1
        
        -- 获取当前子弹的补偿值（小数）
        local rawY, rawX = getBulletRecoil(currentBullet)
        
        -- 应用误差累加，转换为整数移动量
        local moveY, moveX = applyMovement(rawY, rawX)
        
        -- 记录移动量(用于复位)
        totalMoveY = totalMoveY + moveY
        totalMoveX = totalMoveX + moveX
        
        -- 执行鼠标移动补偿
        if moveY ~= 0 or moveX ~= 0 then
            MoveMouseRelative(moveX, moveY)
        end
        
        log("Bullet #%d: raw=(%.2f,%.2f) move=(%d,%d) err=(%.2f,%.2f)", 
            currentBullet, rawY, rawX, moveY, moveX, errorY, errorX)
        
        -- 等待下一发
        Sleep(sleepTime)
        
    until not IsMouseButtonPressed(clickBtn)
    
    log("Stop at bullet #%d, totalY=%d, totalX=%d", currentBullet, totalMoveY, totalMoveX)
    
    -- 鼠标复位
    if resetPointState and (totalMoveY ~= 0 or totalMoveX ~= 0) then
        resetMousePosition()
    end
end

-- 复位鼠标位置
function resetMousePosition()
    log("Resetting mouse position...")
    
    -- 快速复位
    local steps = 10
    local stepY = math.floor(-totalMoveY / steps)
    local stepX = math.floor(-totalMoveX / steps)
    
    for i = 1, steps do
        MoveMouseRelative(stepX, stepY)
        Sleep(1)
    end
    
    -- 补偿余数
    local remainY = -totalMoveY - (stepY * steps)
    local remainX = -totalMoveX - (stepX * steps)
    if remainY ~= 0 or remainX ~= 0 then
        MoveMouseRelative(remainX, remainY)
    end
end

-- 复位配置
function resetConfig()
    log("Config reset")
    currentGunIndex = 1
    recoilEnabled = false
    resetPointState = false
    log("Current gun: %s", getCurrentGun().name)
end
