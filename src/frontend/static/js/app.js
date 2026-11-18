async function checkStatus() {

    try {

        const response = await fetch("/api/status");
        const data = await response.json();

        console.log("Player status:", data);

    } catch (error) {

        console.error("Could not connect to player:", error);

    }

}

checkStatus();