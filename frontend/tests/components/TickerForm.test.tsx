import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TickerForm } from "../../src/components/TickerForm";

describe("TickerForm", () => {
  it("trims and upper-cases the ticker before searching", async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(<TickerForm onSearch={onSearch} loading={false} />);

    await user.type(screen.getByLabelText("Stock ticker"), "  msft ");
    await user.click(screen.getByRole("button", { name: "Get brief" }));

    expect(onSearch).toHaveBeenCalledExactlyOnceWith("MSFT");
  });

  it("submits on Enter", async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(<TickerForm onSearch={onSearch} loading={false} />);

    await user.type(screen.getByLabelText("Stock ticker"), "nvda{Enter}");

    expect(onSearch).toHaveBeenCalledWith("NVDA");
  });

  it("disables submit while the input is empty or whitespace", async () => {
    const user = userEvent.setup();
    render(<TickerForm onSearch={vi.fn()} loading={false} />);
    const submit = screen.getByRole("button", { name: "Get brief" });

    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText("Stock ticker"), "   ");
    expect(submit).toBeDisabled();
  });

  it("searches immediately when a popular chip is clicked", async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(<TickerForm onSearch={onSearch} loading={false} />);

    await user.click(screen.getByRole("button", { name: "TSLA" }));

    expect(onSearch).toHaveBeenCalledWith("TSLA");
    expect(screen.getByLabelText("Stock ticker")).toHaveValue("TSLA");
  });

  it("Input and every button are disabled while loading", () => {
    render(<TickerForm onSearch={vi.fn()} loading={true} />);

    expect(screen.getByRole("textbox", { name: "Stock ticker" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Loading…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "AAPL" })).toBeDisabled();
  });

  it("Input and every button are enabled when not loading", async () => {
    const user = userEvent.setup();
    render(<TickerForm onSearch={vi.fn()} loading={false} />);
    const input = screen.getByRole("textbox", { name: "Stock ticker" });

    expect(input).toBeEnabled();
    expect(screen.getByRole("button", { name: "AAPL" })).toBeEnabled();

    await user.type(input, "aapl");
    expect(screen.getByRole("button", { name: "Get brief" })).toBeEnabled();
  });
});
