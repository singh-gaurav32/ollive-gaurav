import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CancelButton } from "./CancelButton";

describe("CancelButton", () => {
  it("calls onCancel when clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<CancelButton onCancel={onCancel} />);
    await user.click(screen.getByTestId("cancel-button"));

    expect(onCancel).toHaveBeenCalledOnce();
  });
});
