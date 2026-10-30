import type { DetailedHTMLProps, HTMLAttributes } from 'react';

type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
  variant?: string;
  size?: string;
  label?: string;
  name?: string;
  disabled?: boolean;
  open?: boolean;
};

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'ui-button': UieProps;
      'ui-input': UieProps;
      'ui-dialog': UieProps;
      'ui-tabs': UieProps;
      'ui-checkbox': UieProps;
      'ui-select': UieProps;
      'ui-tooltip': UieProps;
      'ui-toast': UieProps;
      'ui-menu': UieProps;
    }
  }
}

export {};
