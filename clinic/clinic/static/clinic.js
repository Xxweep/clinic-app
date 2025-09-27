
// التعامل مع إنهاء الخدمة
document.querySelectorAll(".end-service").forEach(button => {
  button.addEventListener("click", function () {
    const row = this.closest("tr");
    const name = row.querySelector("td:first-child").innerText;

    const completedList = document.getElementById("completed-list");
    const li = document.createElement("li");
    li.textContent = `${name} - تمت الخدمة`;
    completedList.appendChild(li);

    row.remove();
  });
});


// زر تحميل الجدول كـ Excel
document.getElementById("downloadExcel").addEventListener("click", function () {
    let table = document.getElementById("patientsTable");
    let rows = [];

    for (let i = 0; i < table.rows.length; i++) {
        let row = [], cols = table.rows[i].cells;
        for (let j = 0; j < cols.length; j++) {
            row.push(cols[j].innerText);
        }
        rows.push(row.join(","));
    }

    let csvContent = "data:text/csv;charset=utf-8," + rows.join("\n");
    let link = document.createElement("a");
    link.setAttribute("href", encodeURI(csvContent));
    link.setAttribute("download", "patients.csv");
    document.body.appendChild(link);
    link.click();
});

// زر "تمت الخدمة"
document.querySelectorAll(".done-btn").forEach(btn => {
    btn.addEventListener("click", function () {
        this.parentElement.innerHTML = "✔️ تمت الخدمة";
    });
});


    function updateAdminView() {
        fetch("{{ url_for('queue_data') }}")
            .then(response => response.json())
            .then(data => {
                // تحديث جدول الانتظار
                const queueBody = document.querySelector('#patientsTable tbody');
                queueBody.innerHTML = ''; // إفراغ الجدول الحالي
                data.queue.forEach((p, index) => {
                    const returningTag = p.is_returning ? `<span class="returning-tag">(زيارة متكررة)</span>` : '';
                    const historyNotes = p.history.length > 0 ? `<ul>${p.history.map(note => `<li>${note}</li>`).join('')}</ul>` : 'لا يوجد';
                    
                    const row = `
                        <tr>
                            <td data-label="التسلسل">${index + 1}</td>
                            <td data-label="الاسم">${p.name} ${returningTag}</td>
                            <td data-label="العمر">${p.age}</td>
                            <td data-label="الجنس">${p.gender}</td>
                            <td data-label="الحساسية">${p.allergies}</td>
                            <td data-label="التاريخ المرضي">${historyNotes}</td>
                            <td data-label="الإجراءات" class="action-buttons">
                                <form action="/done/${index}" method="POST"><button class="btn-done">تمت الخدمة</button></form>
                                <form action="/cancel_admin/${index}" method="POST"><button class="btn-cancel-admin">إلغاء</button></form>
                            </td>
                        </tr>
                    `;
                    queueBody.innerHTML += row;
                });

                // تحديث جدول السجل
                const servedBody = document.querySelector('#servedTable tbody');
                servedBody.innerHTML = '';
                data.done_queue.forEach(p => {
                    const statusClass = p.status === 'تمت الخدمة' ? 'status-done' : 'status-cancelled';
                    const historyNotes = p.history.length > 0 ? `<ul>${p.history.map(note => `<li>${note}</li>`).join('')}</ul>` : '<li>لا توجد ملاحظات.</li>';

                    const row = `
                        <tr>
                            <td data-label="الاسم">${p.name}</td>
                            <td data-label="آخر حالة"><span class="${statusClass}">${p.status}</span></td>
                            <td data-label="كامل التاريخ المرضي">${historyNotes}</td>
                            <td data-label="إضافة ملاحظة جديدة">
                                <form action="/add_note/${p.phone}" method="POST">
                                    <input type="text" name="note" placeholder="ملاحظة الطبيب" required>
                                    <button type="submit" class="btn-primary">حفظ</button>
                                </form>
                            </td>
                        </tr>
                    `;
                    servedBody.innerHTML += row;
                });
            });
    }

    // استدعاء الدالة كل 5 ثوانٍ
    setInterval(updateAdminView, 5000);

      const modal = document.getElementById('doneModal');
        const form = document.getElementById('doneForm');
        const patientNameSpan = document.getElementById('modalPatientName');

        function openDoneModal(position, patientName) {
            // تحديث رابط الفورم ليرسل إلى المريض الصحيح
            form.action = `/done/${position}`;
            // تحديث اسم المريض في النافذة
            patientNameSpan.textContent = patientName;
            // إظهار النافذة
            modal.style.display = 'block';
        }

        function closeDoneModal() {
            modal.style.display = 'none';
        }

        // إغلاق النافذة عند الضغط خارجها
        window.onclick = function(event) {
            if (event.target == modal) {
                closeDoneModal();
            }
        }



    // طلب إذن الإشعارات فوراً عند دخول الصفحة
    if ('Notification' in window) {
        Notification.requestPermission();
    }

    function updateQueueStatus() {
        // احصل على رقم العميل الحالي من الصفحة
    // يجب تمرير هذه القيم من الخادم إلى الصفحة عبر عناصر البيانات أو متغيرات جافاسكريبت
    // مثال: <script>const currentPosition = {{ position|tojson }}; const queueLength = {{ queue|length|tojson }}; const clientServed = {{ client_served|tojson }};</script>
    // أو عبر عناصر data-* في HTML
    
    // مثال على تعريف المتغيرات (استبدل القيم الحقيقية من الخادم)
    const currentPosition = window.currentPosition || 1; // يجب تعيين القيمة الحقيقية من الخادم
    const initialQueueLength = window.queueLength || 1; // يجب تعيين القيمة الحقيقية من الخادم
    const clientServed = window.clientServed || false; // يجب تعيين القيمة الحقيقية من الخادم
    
    function updateQueueStatus() {
        fetch("/queue_data")
            .then(response => response.json())
            .then(data => {
                const totalBefore = currentPosition - (initialQueueLength - data.queue_length);
    
                const turnElement = document.querySelector('.turn');
                const positionInfoElement = document.querySelector('.position-info');
    
                if (totalBefore < 0) {
                    // تمت خدمته، قم بتحويله إلى صفحة الشكر
                    window.location.href = "/queue_page?position=9999";
                    return;
                }
    
                if (totalBefore === 0) {
                    turnElement.textContent = 'لقد حان دورك الآن!';
                } else {
                    turnElement.textContent = `أمامك ${totalBefore} شخص`;
                }
                positionInfoElement.textContent = `رقمك في الطابور هو ${totalBefore + 1}`;
    
                // --- منطق الإشعارات ---
                // أرسل إشعاراً إذا كان أمامه شخصان أو أقل، ولم يتم إرسال إشعار من قبل
                if (totalBefore <= 2 && totalBefore > 0 && Notification.permission === 'granted' && !sessionStorage.getItem('notification_sent')) {
                    const notification = new Notification('عيادة الشفاء', {
                        body: `دورك اقترب! أمامك ${totalBefore} شخص فقط. الرجاء الاستعداد.`,
                        icon: "/static/logo.png" // اختياري: يمكنك وضع شعار العيادة في مجلد static
                    });
    
                    // ضع علامة بأن الإشعار قد أُرسل، لمنع تكراره
                    sessionStorage.setItem('notification_sent', 'true');
                }
            });
    }
    
    // لا تقم بتشغيل التحديث إذا كان العميل قد تمت خدمته بالفعل
    if (!clientServed) {
        setInterval(updateQueueStatus, 5000);
    }
        setInterval(updateQueueStatus, 5000);
    }





