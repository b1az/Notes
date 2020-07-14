defmodule Todo.Database do
  use GenServer

  @db_folder "./persist"
  @db_workers 3

  def start do
    IO.puts("db")
    GenServer.start_link(__MODULE__, nil, name: __MODULE__)
  end

  def store(key, data) do
    Todo.DatabaseWorker.store(choose_worker(key), key, data)
  end

  def get(key) do
    Todo.DatabaseWorker.get(choose_worker(key), key)
  end

  @impl GenServer
  def init(_) do
    File.mkdir_p!(@db_folder)
    {:ok, start_workers()}
  end

  @impl GenServer
  def handle_call({:choose_worker, key}, _, state) do
    worker_idx = :erlang.phash2(key, @db_workers)
    {:reply, Map.get(state, worker_idx), state}
  end

  defp choose_worker(key) do
    GenServer.call(__MODULE__, {:choose_worker, key})
  end

  defp start_workers() do
    Enum.reduce(0..@db_workers-1, %{}, fn idx, acc ->
      {:ok, pid} = Todo.DatabaseWorker.start_link(@db_folder)
      Map.put(acc, idx, pid)
    end)
  end
end

