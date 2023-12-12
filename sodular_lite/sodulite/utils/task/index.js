
class Queue {
    constructor() {
        this.queue = [];
        this.isProcessing = false;
    }

    async add(task) {
        return new Promise((resolve) => {
            this.queue.push({ task, resolve });
            if (!this.isProcessing) {
                this.#processQueue();
            }
        });
    }

    async #processQueue() {
        if (this.queue.length === 0) {
            this.isProcessing = false;
            return;
        }

        this.isProcessing = true;
        const { task, resolve } = this.queue.shift();

        try {
            const result = await task();
            resolve(result); // Resolve with the result of the task
        } catch (error) {
            // Handle errors here
            resolve(null); // Resolve with null if there was an error
        }

        await this.#processQueue();
    }
}
export default Queue