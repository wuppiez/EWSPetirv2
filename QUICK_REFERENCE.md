# 🚀 QUICK REFERENCE CARD - EWS Longsor v2.0

## ⚡ Startup Commands

```bash
# Terminal 1 - Bot Listener (MUST RUN 24/7)
python telegram_bot_listener.py

# Terminal 2 - Dashboard
streamlit run bogor_v2_advanced.py
```

---

## 🔑 Critical Files

| File | Purpose | Location | Must Edit? |
|------|---------|----------|------------|
| `telegram_bot_listener.py` | Bot service | Root | ✅ Token |
| `bogor_v2_advanced.py` | Dashboard | Root | ✅ Token |
| `risk_scoring.py` | Scoring logic | Root | ❌ (unless customize) |
| `telegram_subscribers.json` | User data | Auto-gen | ❌ Never |
| `requirements.txt` | Dependencies | Root | ❌ No |

---

## 🎯 Quick Troubleshooting

### Problem: Bot tidak respon
```bash
# Check 1: Bot running?
ps aux | grep telegram_bot_listener

# Check 2: Token benar?
curl https://api.telegram.org/bot<TOKEN>/getMe

# Fix: Restart bot
pkill -f telegram_bot_listener
python telegram_bot_listener.py
```

### Problem: Dashboard error
```bash
# Check logs
tail -f ~/.streamlit/logs/*.log

# Restart
Ctrl+C
streamlit run bogor_v2_advanced.py
```

### Problem: BMKG API gagal
```
# Normal - BMKG API kadang lambat
# Tunggu 30 detik, cache 10 menit
# Refresh browser atau tunggu auto-update
```

---

## 📊 Risk Score Interpretation

| Score | Status | Emoji | Action |
|-------|--------|-------|--------|
| 0-40 | AMAN | 🟢 | Normal monitoring |
| 41-70 | WASPADA | 🟡 | Prepare evacuation |
| 71-100 | BAHAYA | 🔴 | Evacuate immediately |

---

## 🔧 Common Tasks

### Add New Subscriber Manually (if needed)
```json
// Edit telegram_subscribers.json
{
  "subscribers": [
    {
      "chat_id": "123456789",
      "username": "user123",
      "first_name": "John",
      "registered_at": "2025-11-03T10:00:00",
      "active": true
    }
  ]
}
```

### Change Thresholds
```python
# Edit risk_scoring.py, line ~50
"rainfall_hourly": {
    "aman": {"max": 5, ...},     # Change here
    "waspada": {"min": 5, "max": 15, ...},
    "bahaya": {"min": 15, ...}
}
```

### Change Bot Token (if compromised)
```python
# 1. Get new token from @BotFather
# 2. Edit bogor_v2_advanced.py line ~106
TELEGRAM_BOT_TOKEN = "NEW_TOKEN_HERE"

# 3. Edit telegram_bot_listener.py line ~34
TELEGRAM_BOT_TOKEN = "NEW_TOKEN_HERE"

# 4. Restart both services
```

---

## 📱 Bot Commands (for testing)

```
/start  - Register untuk notifikasi
/stop   - Berhenti notifikasi
/status - Cek status registrasi
/info   - Info sistem
/help   - Bantuan
```

---

## 🔍 Monitoring Checklist

### Daily ✅
- [ ] Dashboard accessible (http://localhost:8501)
- [ ] Bot listener running (check terminal)
- [ ] No errors in logs
- [ ] Last update timestamp current

### Weekly ✅
- [ ] Backup telegram_subscribers.json
- [ ] Review false alarm rate
- [ ] Test notification delivery
- [ ] Check disk space

### Monthly ✅
- [ ] Review system performance
- [ ] Update documentation if needed
- [ ] Analyze new data patterns
- [ ] Check for software updates

---

## 📊 Key Metrics to Monitor

```
✅ Uptime: Should be > 99%
✅ Response time: < 1 sec for bot
✅ False alarm rate: < 5%
✅ Notification delivery: > 95%
✅ API calls: ~6/hour (10 min cache)
```

---

## 🆘 Emergency Contacts

```
BPBD Bogor:    (0251) 8324000
SAR:           115
Ambulans:      118 / 119
BMKG Bogor:    (0251) 8311511
PMI:           (0251) 8321111
```

---

## 💾 Backup Commands

```bash
# Backup subscribers
cp telegram_subscribers.json backup/subscribers_$(date +%Y%m%d).json

# Backup config
cp risk_scoring_config.json backup/config_$(date +%Y%m%d).json

# Backup all
tar -czf ews_backup_$(date +%Y%m%d).tar.gz *.py *.json *.md
```

---

## 🔄 Update/Restart Procedure

```bash
# 1. Stop services
pkill -f telegram_bot_listener
# Ctrl+C on dashboard terminal

# 2. Backup data
cp telegram_subscribers.json telegram_subscribers.backup.json

# 3. Update code (if needed)
git pull  # or copy new files

# 4. Restart services
python telegram_bot_listener.py &
streamlit run bogor_v2_advanced.py
```

---

## 📈 Performance Benchmarks

```
✅ Bot response: < 1 second
✅ Dashboard load: < 3 seconds
✅ Risk calculation: < 0.1 second
✅ Notification send: < 5 seconds
✅ Memory usage: ~100 MB
✅ CPU usage: < 5% idle, < 20% active
```

---

## 🎓 Training Resources

For detailed information, read:
1. `INSTALLATION_GUIDE.md` - Setup & troubleshooting
2. `README_EWS_v2.md` - Complete documentation
3. `FINAL_REPORT.md` - Full system report
4. `SUMMARY.md` - Quick overview

---

## ⚠️ Important Notes

1. **NEVER** commit bot token to Git
2. **ALWAYS** backup telegram_subscribers.json
3. **MONITOR** logs for errors daily
4. **TEST** notification delivery weekly
5. **UPDATE** thresholds if local conditions change
6. **DOCUMENT** any customizations made
7. **TRAIN** backup admin for continuity

---

## 🏆 Success Indicators

Your system is running well if:
- ✅ Dashboard shows current data
- ✅ Status updates every 10 minutes
- ✅ Bot responds to /start instantly
- ✅ Notifications delivered < 5 sec
- ✅ No errors in terminal/logs
- ✅ Subscribers can /start successfully
- ✅ Risk score makes sense vs weather

---

## 📞 Getting Help

If stuck:
1. Check this quick reference
2. Review INSTALLATION_GUIDE.md
3. Search error message in logs
4. Check GitHub issues (if available)
5. Contact tech support
6. Join community forum (if available)

---

## 🔐 Security Reminders

```
❌ Never share bot token publicly
❌ Never commit credentials to Git
❌ Never expose dashboard publicly (use firewall)
✅ Use HTTPS in production
✅ Regular security updates
✅ Monitor for suspicious activity
✅ Backup data regularly
```

---

## 📋 Pre-Flight Checklist (Before Going Live)

```
[ ] Bot token configured correctly
[ ] Bot tested with /start command
[ ] Dashboard loads without errors
[ ] BMKG API connection working
[ ] Thresholds reviewed and validated
[ ] Emergency contacts updated
[ ] Backup procedure documented
[ ] Admin trained on operations
[ ] User guide distributed to community
[ ] Monitoring system in place
[ ] Escalation procedure defined
[ ] Backup admin assigned
```

---

## 🎯 Quick Command Reference

```bash
# Check if processes running
ps aux | grep -E "telegram_bot_listener|streamlit"

# View logs
tail -f logs/bot.log          # Bot logs
tail -f ~/.streamlit/logs/*.log  # Dashboard logs

# Restart everything
./restart_all.sh  # If you create this script

# Test bot
curl https://api.telegram.org/bot<TOKEN>/getMe

# Test dashboard
curl http://localhost:8501

# Check ports
netstat -tuln | grep 8501
```

---

**Keep this file handy for daily operations!**

**Version**: 2.0  
**Last Updated**: November 2025  
**Print & Post**: Near server/workstation ✅
