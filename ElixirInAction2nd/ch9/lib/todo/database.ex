defmodule Todo.Database do
  @db_folder "./persist"
  @db_workers 3

  def start_link(_) do
    IO.puts("db")
    File.mkdir_p!(@db_folder)
    children = Enum.map(0..@db_workers-1, &worker_spec/1)
    Supervisor.start_link(children, strategy: :one_for_one)
  end

  def store(key, data) do
    Todo.DatabaseWorker.store(choose_worker(key), key, data)
  end

  def get(key) do
    Todo.DatabaseWorker.get(choose_worker(key), key)
  end

  defp choose_worker(key) do
    :erlang.phash2(key, @db_workers)
  end

  def child_spec(_) do
    %{
      id: __MODULE__,
      start: {__MODULE__, :start_link, [nil]},
      type: :supervisor
    }
  end

  defp worker_spec(worker_id) do
    default_worker_spec = {Todo.DatabaseWorker, {@db_folder, worker_id}}
    Supervisor.child_spec(default_worker_spec, id: worker_id)
  end
end
