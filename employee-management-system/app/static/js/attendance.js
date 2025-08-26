document.addEventListener('DOMContentLoaded', function() {
    const employeeId = document.getElementById('employeeId').value;
    const attendanceStatusElement = document.getElementById('attendanceStatus');
    const clockInOutButton = document.getElementById('clockInOutButton');
    const currentTimeElement = document.getElementById('currentTime');

    let isCurrentlyClockedIn = isClockedIn; // Initialize with value from Jinja

    function updateCurrentTime() {
        const now = new Date();
        currentTimeElement.textContent = now.toLocaleTimeString();
    }

    setInterval(updateCurrentTime, 1000);
    updateCurrentTime(); // Initial call

    function updateAttendanceUI() {
        if (isCurrentlyClockedIn) {
            attendanceStatusElement.textContent = 'Clocked In';
            clockInOutButton.textContent = 'Clock Out';
            clockInOutButton.classList.remove('btn-primary');
            clockInOutButton.classList.add('btn-danger');
        } else {
            attendanceStatusElement.textContent = 'Clocked Out';
            clockInOutButton.textContent = 'Clock In';
            clockInOutButton.classList.remove('btn-danger');
            clockInOutButton.classList.add('btn-primary');
        }
    }

    clockInOutButton.addEventListener('click', async function() {
        const action = isCurrentlyClockedIn ? 'clock_out' : 'clock_in';
        const endpoint = `/api/attendance/${action}`;

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ employee_id: employeeId })
            });
            const data = await response.json();
            if (data.status === 'success') {
                isCurrentlyClockedIn = !isCurrentlyClockedIn; // Toggle status
                updateAttendanceUI(); // Update UI based on new status
            } else {
                alert('Error: ' + data.message);
            }
        } catch (error) {
            console.error('Error performing attendance action:', error);
            alert('An error occurred during attendance action.');
        }
    });

    updateAttendanceUI(); // Initial UI setup
});