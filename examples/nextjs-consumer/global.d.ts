import type { DetailedHTMLProps, HTMLAttributes } from 'react';

type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & Record<string, any>;

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'ui-button': UieProps;
      'ui-checkbox': UieProps;
      'ui-dialog': UieProps;
      'ui-input': UieProps;
      'ui-menu': UieProps;
      'ui-select': UieProps;
      'ui-tabs': UieProps;
      'ui-toast': UieProps;
      'ui-tooltip': UieProps;
    }
  }
}

export {};
