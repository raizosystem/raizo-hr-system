// وظيفة تأكيد حذف الموظف
function confirmDelete(employeeId, employeeName) {
    if (confirm('هل أنت متأكد من حذف الموظف: ' + employeeName + '؟\nسيتم تغيير حالة الموظف إلى غير نشط.')) {
        // إرسال طلب حذف
        fetch('/delete_employee/' + employeeId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // إعادة تحميل الصفحة لإظهار التغييرات
                location.reload();
            } else {
                alert('حدث خطأ أثناء حذف الموظف: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('حدث خطأ أثناء حذف الموظف');
        });
    }
}

// تهيئة Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة tooltips إذا كانت موجودة
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // تهيئة modals
    var modalList = [].slice.call(document.querySelectorAll('.modal'));
    modalList.forEach(function(modalEl) {
        new bootstrap.Modal(modalEl);
    });
});

// وظيفة لإظهار رسائل التنبيه
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // إضافة التنبيه في أعلى الصفحة
    const container = document.querySelector('main');
    container.insertBefore(alertDiv, container.firstChild);
    
    // إزالة التنبيه تلقائياً بعد 5 ثوان
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Image Error Handling
document.addEventListener('DOMContentLoaded', function() {
    // Handle image loading errors
    const images = document.querySelectorAll('img[alt="صورة الموظف"]');
    
    images.forEach(function(img) {
        img.addEventListener('error', function() {
            // Hide the broken image
            this.style.display = 'none';
            
            // Show placeholder if it exists
            const placeholder = this.nextElementSibling;
            if (placeholder && placeholder.classList.contains('employee-avatar-placeholder')) {
                placeholder.style.display = 'flex';
            } else if (placeholder && placeholder.classList.contains('rounded-circle')) {
                placeholder.style.display = 'flex';
            }
        });
        
        // Add loading state
        img.addEventListener('loadstart', function() {
            this.style.opacity = '0.5';
        });
        
        img.addEventListener('load', function() {
            this.style.opacity = '1';
        });
    });
    
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
});

// إصلاح مشاكل التحريف والعرض
document.addEventListener('DOMContentLoaded', function() {
    // منع التحريف الأفقي
    document.body.style.overflowX = 'hidden';
    document.documentElement.style.overflowX = 'hidden';
    
    // إصلاح عرض الحاوي
    const containers = document.querySelectorAll('.container-fluid');
    containers.forEach(container => {
        container.style.maxWidth = '100%';
        container.style.overflowX = 'hidden';
    });
    
    // إصلاح مشاكل الصفوف والأعمدة
    const rows = document.querySelectorAll('.row');
    rows.forEach(row => {
        row.style.marginLeft = '0';
        row.style.marginRight = '0';
    });
    
    // مراقبة تغيير حجم النافذة
    window.addEventListener('resize', function() {
        document.body.style.overflowX = 'hidden';
        document.documentElement.style.overflowX = 'hidden';
    });
});

// تحدية التنبيهات
// تحديث التنبيهات تلقائياً
// تحديث التنبيهات
// تحديث التنبيهات - نسخة محسنة ومُحدثة
function updateNotifications() {
    console.log('🔄 بدء تحديث الإشعارات...');
    
    fetch('/api/notifications?unread_only=false&limit=5')
        .then(response => {
            console.log('📡 حالة الاستجابة:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 البيانات المستلمة:', data);
            
            // العثور على العناصر المطلوبة
            const bellIcon = document.querySelector('#notificationsDropdown');
            const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
            let badge = document.querySelector('#notificationsDropdown .badge');
            
            if (!bellIcon) {
                console.error('❌ لم يتم العثور على أيقونة الجرس!');
                return;
            }
            
            console.log(`📬 عدد الإشعارات غير المقروءة: ${data.unread_count}`);
            
            // تحديث أو إنشاء العداد
            if (data.unread_count > 0) {
                if (!badge) {
                    // إنشاء شارة جديدة
                    badge = document.createElement('span');
                    badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
                    bellIcon.appendChild(badge);
                    console.log('✅ تم إنشاء شارة العداد');
                }
                
                badge.textContent = data.unread_count;
                badge.style.display = 'inline-block';
                console.log(`✅ تم تحديث العداد: ${data.unread_count}`);
                
                // تحديث محتوى القائمة المنسدلة
                if (dropdownMenu && data.notifications && data.notifications.length > 0) {
                    updateNotificationsDropdown(dropdownMenu, data.notifications);
                }
            } else {
                console.log('📭 لا توجد إشعارات غير مقروءة');
                if (badge) {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('❌ خطأ في تحديث الإشعارات:', error);
        });
}

// دالة تحديث محتوى القائمة المنسدلة
function updateNotificationsDropdown(dropdownMenu, notifications) {
    // البحث عن منطقة الإشعارات الديناميكية
    let dynamicArea = dropdownMenu.querySelector('.dynamic-notifications');
    
    if (!dynamicArea) {
        // إنشاء منطقة جديدة
        dynamicArea = document.createElement('div');
        dynamicArea.className = 'dynamic-notifications';
        
        // إدراجها في المكان المناسب
        const firstDivider = dropdownMenu.querySelector('.dropdown-divider');
        if (firstDivider) {
            dropdownMenu.insertBefore(dynamicArea, firstDivider.nextElementSibling);
        } else {
            dropdownMenu.appendChild(dynamicArea);
        }
    }
    
    // مسح المحتوى السابق
    dynamicArea.innerHTML = '';
    
    // إضافة الإشعارات الجديدة
    notifications.forEach((notification, index) => {
        const notificationElement = document.createElement('li');
        notificationElement.innerHTML = `
            <div class="dropdown-item notification-item ${!notification.is_read ? 'unread' : ''}">
                <div class="d-flex align-items-start">
                    <div class="notification-icon me-2">
                        <i class="fas fa-${getNotificationIcon(notification.notification_type)} text-${getNotificationColor(notification.notification_type)}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1 fw-bold">${notification.title}</h6>
                        <p class="mb-1 small text-muted">${notification.message}</p>
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            ${formatNotificationDate(notification.created_at)}
                        </small>
                    </div>
                    ${!notification.is_read ? '<div class="unread-indicator"><span class="badge bg-primary">جديد</span></div>' : ''}
                </div>
            </div>
        `;
        dynamicArea.appendChild(notificationElement);
    });
    
    console.log(`✅ تم تحديث ${notifications.length} إشعارات في القائمة`);
}

// دوال مساعدة محسنة
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'times-circle',
        'info': 'info-circle',
        'system': 'cog'
    };
    return icons[type] || 'bell';
}

function getNotificationColor(type) {
    const colors = {
        'success': 'success',
        'warning': 'warning',
        'error': 'danger',
        'info': 'info',
        'system': 'secondary'
    };
    return colors[type] || 'primary';
}

function formatNotificationDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'الآن';
    if (diffMins < 60) return `منذ ${diffMins} دقيقة`;
    if (diffHours < 24) return `منذ ${diffHours} ساعة`;
    if (diffDays < 7) return `منذ ${diffDays} يوم`;
    
    return date.toLocaleDateString('ar-SA', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// تشغيل التحديث عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 تم تحميل الصفحة - بدء نظام الإشعارات');
    
    // تحديث فوري
    setTimeout(updateNotifications, 1000);
    
    // تحديث دوري كل 30 ثانية
    setInterval(updateNotifications, 30000);
    
    console.log('⏰ تم تفعيل التحديث الدوري للإشعارات');
});